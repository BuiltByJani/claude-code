#!/usr/bin/env python3
"""Editing / Cuts: remove silences from a talking-head video.

Usage:
  python scripts/cut_silences.py raw.mov exports/job1/01_cut.mp4 --threshold -35 --min-silence 0.35 --padding 120
Writes the cut video plus <output>.cuts.json (kept segments, silences removed, durations).
"""
import argparse
import json
import re
import subprocess
from pathlib import Path


def detect_silences(src, threshold, min_sil):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", src, "-af", f"silencedetect=noise={threshold}dB:d={min_sil}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
        capture_output=True, text=True).stdout.strip())
    if len(ends) < len(starts):
        ends.append(dur)
    return list(zip(starts, ends)), dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--threshold", type=float, default=-35, help="dB below which audio counts as silence")
    ap.add_argument("--min-silence", type=float, default=0.35, help="seconds")
    ap.add_argument("--padding", type=int, default=120, help="ms of breathing room kept each side of speech")
    a = ap.parse_args()

    sils, dur = detect_silences(a.src, a.threshold, a.min_silence)
    pad = a.padding / 1000
    keep, cursor = [], 0.0
    for s, e in sils:
        cut_s, cut_e = max(s + pad, cursor), max(e - pad, cursor)
        if cut_s > cursor:
            keep.append((cursor, cut_s))
        cursor = max(cursor, cut_e)
    if cursor < dur:
        keep.append((cursor, dur))
    keep = [(round(s, 3), round(e, 3)) for s, e in keep if e - s > 0.05]
    if not keep:
        raise SystemExit("Everything was detected as silence — raise --threshold (e.g. -45).")

    has_audio = "audio" in subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", a.src],
        capture_output=True, text=True).stdout
    parts, labels = [], ""
    for i, (s, e) in enumerate(keep):
        parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        labels += f"[v{i}]"
        if has_audio:
            parts.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS[a{i}]")
            labels += f"[a{i}]"
    parts.append(f"{labels}concat=n={len(keep)}:v=1:a={1 if has_audio else 0}[v]" + ("[a]" if has_audio else ""))
    Path(a.dst).parent.mkdir(parents=True, exist_ok=True)
    script = Path(a.dst).with_suffix(".filter.txt")
    script.write_text(";\n".join(parts))
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", a.src, "-filter_complex_script", str(script), "-map", "[v]"]
    if has_audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", a.dst]
    subprocess.run(cmd, check=True)
    script.unlink()

    new_dur = sum(e - s for s, e in keep)
    report = {"source": a.src, "output": a.dst, "silences_removed": len(sils),
              "original_seconds": round(dur, 2), "new_seconds": round(new_dur, 2),
              "padding_ms": a.padding, "kept_segments": keep}
    Path(a.dst + ".cuts.json").write_text(json.dumps(report, indent=2))
    print(f"Removed {len(sils)} silences: {dur:.1f}s -> {new_dur:.1f}s  ({a.dst})")


if __name__ == "__main__":
    main()
