#!/usr/bin/env python3
"""Archive / B-roll finder: match each line of a script to library clips.

Usage:
  python scripts/broll_find.py --script exports/job1/script.txt --top 5 --orientation vertical
  python scripts/broll_find.py --text "walking into the gym at 5am" --top 5

Uses CLIP embeddings when library/embeddings.npy exists (semantic: finds a gym shot even if
nobody typed "gym"); otherwise keyword overlap with Tagger captions/tags.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "library"
STOP = set("a an the and or but to of in on at for with is are was were be i you my your it this that so just".split())


def words(s):
    return {w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOP and len(w) > 2}


def load():
    recs = {}
    for line in (LIB / "index.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            recs[r["id"]] = r
    return recs


def eligible(r, orientation, videos_only):
    if r["type"] == "error":
        return False
    if videos_only and r["type"] != "video":
        return False
    if orientation and r.get("orientation") != orientation:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script")
    ap.add_argument("--text")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--orientation", choices=["vertical", "horizontal", "square"])
    ap.add_argument("--videos-only", action="store_true")
    a = ap.parse_args()
    text = Path(a.script).read_text() if a.script else (a.text or "")
    beats = [b.strip(" -•\t") for b in text.splitlines() if b.strip()]
    recs = load()

    clip = None
    if (LIB / "embeddings.npy").exists():
        try:
            import numpy as np
            import open_clip
            import torch
            model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
            tok = open_clip.get_tokenizer("ViT-B-32")
            emb = np.load(LIB / "embeddings.npy").astype("float32")
            ids = json.loads((LIB / "embedding_ids.json").read_text())
            clip = (model, tok, emb, ids, torch)
        except ImportError:
            pass

    out = []
    for beat in beats:
        scored = []
        if clip:
            model, tok, emb, ids, torch = clip
            with torch.no_grad():
                t = model.encode_text(tok([beat]))
                t = (t / t.norm(dim=-1, keepdim=True)).numpy()[0]
            sims = emb @ t
            for i in sims.argsort()[::-1]:
                r = recs.get(ids[i])
                if r and eligible(r, a.orientation, a.videos_only):
                    scored.append((float(sims[i]), r))
                if len(scored) >= a.top:
                    break
        else:
            bw = words(beat)
            for r in recs.values():
                if not eligible(r, a.orientation, a.videos_only):
                    continue
                rw = words(r.get("caption", "") + " " + " ".join(r.get("tags", [])))
                s = len(bw & rw) + (0.5 if r["type"] == "video" else 0)
                if bw & rw:
                    scored.append((s, r))
            scored.sort(key=lambda x: -x[0])
            scored = scored[: a.top]
        out.append({
            "beat": beat,
            "method": "clip" if clip else "keywords",
            "candidates": [
                {"id": r["id"], "score": round(s, 3), "path": r["path"], "type": r["type"],
                 "duration": r.get("duration"), "caption": r.get("caption"), "thumbs": r.get("thumbs")}
                for s, r in scored
            ],
        })
    print(json.dumps(out, indent=2))
    if not clip and not any(o["candidates"] for o in out):
        print("\nNo matches: library has no captions/tags yet and no embeddings. "
              "Run the Tagger or `scan_library.py <folder> --embed` first.")


if __name__ == "__main__":
    main()
