#!/usr/bin/env python3
"""Archive / Scanner: index a photo + video library for B-roll search.

Usage:
  python scripts/scan_library.py ~/Pictures/Export            # incremental scan
  python scripts/scan_library.py ~/Pictures/Export --embed    # + CLIP embeddings (semantic search)
  python scripts/scan_library.py --set-caption <id> "sunset on the pier" --tags beach,golden-hour
  python scripts/scan_library.py --stats

Writes library/index.jsonl (one record per file), library/thumbs/<id>_N.jpg keyframes,
and with --embed library/embeddings.npy + library/embedding_ids.json.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "library"
INDEX = LIB / "index.jsonl"
THUMBS = LIB / "thumbs"

IMG_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".tif", ".tiff"}
VID_EXT = {".mov", ".mp4", ".m4v", ".avi", ".mkv", ".3gp"}


def load_index():
    recs = {}
    if INDEX.exists():
        for line in INDEX.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                recs[r["id"]] = r
    return recs


def save_index(recs):
    LIB.mkdir(exist_ok=True)
    tmp = INDEX.with_suffix(".tmp")
    with tmp.open("w") as f:
        for r in recs.values():
            f.write(json.dumps(r) + "\n")
    tmp.replace(INDEX)


def file_id(path: Path) -> str:
    return hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:16]


def ffprobe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    return json.loads(out.stdout or "{}")


def image_record(path: Path, rid: str) -> dict:
    from PIL import Image, ExifTags
    try:
        import pillow_heif  # noqa: F401
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    rec = {"type": "photo"}
    with Image.open(path) as im:
        w, h = im.size
        exif = {}
        try:
            raw = im.getexif()
            exif = {ExifTags.TAGS.get(k, k): v for k, v in raw.items()}
            sub = raw.get_ifd(0x8769)  # Exif IFD holds DateTimeOriginal
            exif.update({ExifTags.TAGS.get(k, k): v for k, v in sub.items()})
            gps = raw.get_ifd(0x8825)
            if gps:
                rec["gps"] = _gps(gps)
        except Exception:
            pass
        taken = exif.get("DateTimeOriginal") or exif.get("DateTime")
        if taken:
            try:
                rec["taken_at"] = datetime.strptime(str(taken), "%Y:%m:%d %H:%M:%S").isoformat()
            except ValueError:
                pass
        im = im.convert("RGB")
        im.thumbnail((512, 512))
        thumb = THUMBS / f"{rid}_0.jpg"
        im.save(thumb, quality=80)
    rec.update(width=w, height=h, thumbs=[str(thumb.relative_to(ROOT))])
    return rec


def _gps(g):
    def conv(v, ref):
        d, m, s = (float(x) for x in v)
        val = d + m / 60 + s / 3600
        return -val if ref in ("S", "W") else val
    try:
        return {"lat": round(conv(g[2], g[1]), 6), "lon": round(conv(g[4], g[3]), 6)}
    except Exception:
        return None


def video_record(path: Path, rid: str) -> dict:
    info = ffprobe(path)
    fmt = info.get("format", {})
    vs = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    dur = float(fmt.get("duration") or 0)
    w, h = int(vs.get("width") or 0), int(vs.get("height") or 0)
    rot = 0
    for sd in vs.get("side_data_list", []) or []:
        rot = abs(int(sd.get("rotation", 0) or 0))
    if rot in (90, 270):
        w, h = h, w
    fps = 0.0
    if vs.get("avg_frame_rate", "0/0") != "0/0":
        a, b = vs["avg_frame_rate"].split("/")
        fps = round(float(a) / float(b), 2) if float(b) else 0
    tags = fmt.get("tags", {})
    taken = tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time")
    loc = tags.get("com.apple.quicktime.location.ISO6709") or tags.get("location")
    thumbs = []
    for i, frac in enumerate((0.1, 0.5, 0.9)):
        t = THUMBS / f"{rid}_{i}.jpg"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss", f"{dur * frac:.2f}", "-i", str(path),
             "-frames:v", "1", "-vf", "scale=512:-2", str(t)],
            capture_output=True,
        )
        if t.exists():
            thumbs.append(str(t.relative_to(ROOT)))
    return {
        "type": "video", "duration": round(dur, 2), "width": w, "height": h, "fps": fps,
        "has_audio": has_audio, "taken_at": taken, "location_raw": loc, "thumbs": thumbs,
        # B-roll heuristic: short-to-medium clip. Tagger confirms by looking at it.
        "broll_candidate": 1.5 <= dur <= 90,
    }


def scan(roots, embed):
    THUMBS.mkdir(parents=True, exist_ok=True)
    recs = load_index()
    seen = {(r["path"], r.get("mtime")) for r in recs.values()}
    new = errors = 0
    for root in roots:
        root = Path(root).expanduser()
        if not root.exists():
            sys.exit(f"Library folder not found: {root}. Export your photos to a folder on this machine first.")
        for dirpath, _, files in os.walk(root):
            for name in files:
                p = Path(dirpath) / name
                ext = p.suffix.lower()
                if ext not in IMG_EXT | VID_EXT or name.startswith("."):
                    continue
                mtime = int(p.stat().st_mtime)
                if (str(p.resolve()), mtime) in seen:
                    continue
                rid = file_id(p)
                try:
                    base = image_record(p, rid) if ext in IMG_EXT else video_record(p, rid)
                except Exception as e:  # unreadable file: record it, keep going
                    errors += 1
                    base = {"type": "error", "error": str(e)[:200], "thumbs": []}
                w, h = base.get("width") or 0, base.get("height") or 0
                base.update(
                    id=rid, path=str(p.resolve()), mtime=mtime, size=p.stat().st_size,
                    orientation="vertical" if h > w else "horizontal" if w > h else "square",
                    caption=recs.get(rid, {}).get("caption", ""), tags=recs.get(rid, {}).get("tags", []),
                )
                recs[rid] = base
                new += 1
                if new % 500 == 0:
                    save_index(recs)
                    print(f"  ...{new} new files indexed", flush=True)
    save_index(recs)
    print(f"Indexed {new} new files ({errors} unreadable). Library total: {len(recs)}")
    if embed:
        build_embeddings(recs)


def build_embeddings(recs):
    try:
        import numpy as np
        import open_clip
        import torch
        from PIL import Image
    except ImportError:
        sys.exit("--embed needs: pip install open_clip_torch torch numpy")
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model.eval()
    ids, vecs = [], []
    items = [(r["id"], r["thumbs"][len(r["thumbs"]) // 2]) for r in recs.values() if r.get("thumbs")]
    with torch.no_grad():
        for i in range(0, len(items), 64):
            batch = items[i:i + 64]
            imgs = torch.stack([preprocess(Image.open(ROOT / t).convert("RGB")) for _, t in batch])
            v = model.encode_image(imgs)
            v = v / v.norm(dim=-1, keepdim=True)
            vecs.append(v.cpu().numpy())
            ids += [b[0] for b in batch]
            print(f"  embedded {len(ids)}/{len(items)}", flush=True)
    np.save(LIB / "embeddings.npy", np.concatenate(vecs).astype("float16"))
    (LIB / "embedding_ids.json").write_text(json.dumps(ids))
    print(f"Embeddings saved for {len(ids)} items")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roots", nargs="*")
    ap.add_argument("--embed", action="store_true")
    ap.add_argument("--set-caption", nargs=2, metavar=("ID", "CAPTION"))
    ap.add_argument("--tags", default="")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if a.set_caption:
        recs = load_index()
        rid, cap = a.set_caption
        if rid not in recs:
            sys.exit(f"No record {rid}")
        recs[rid]["caption"] = cap
        recs[rid]["tags"] = [t.strip() for t in a.tags.split(",") if t.strip()]
        save_index(recs)
        print(f"Tagged {rid}")
    elif a.stats:
        recs = load_index().values()
        n = lambda f: sum(1 for r in recs if f(r))  # noqa: E731
        print(json.dumps({
            "total": len(recs), "photos": n(lambda r: r["type"] == "photo"),
            "videos": n(lambda r: r["type"] == "video"),
            "broll_candidates": n(lambda r: r.get("broll_candidate")),
            "captioned": n(lambda r: r.get("caption")), "unreadable": n(lambda r: r["type"] == "error"),
        }, indent=2))
    elif a.roots:
        scan(a.roots, a.embed)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
