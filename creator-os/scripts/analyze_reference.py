#!/usr/bin/env python3
"""Research: measure a reference video so the team can copy its technique.

Usage:
  python scripts/analyze_reference.py "https://www.instagram.com/reel/XXXX/"
  python scripts/analyze_reference.py path/to/reference.mp4 [--scene 0.3] [--max-frames 40]

Writes brand/references/<id>/: media/ (video+audio, gitignored), frames/ (a frame at the start
and at every detected cut — the Research agent looks at these for fonts and effects),
report.json (cut times, shots/min, avg shot length, loudness, size), transcript.txt if
faster-whisper is installed.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--scene", type=float, default=0.3, help="cut sensitivity 0-1 (lower = more cuts)")
    ap.add_argument("--max-frames", type=int, default=40)
    a = ap.parse_args()

    rid = hashlib.sha1(a.source.encode()).hexdigest()[:10]
    out = ROOT / "brand" / "references" / rid
    (out / "media").mkdir(parents=True, exist_ok=True)
    (out / "frames").mkdir(exist_ok=True)

    if re.match(r"https?://", a.source):
        if not shutil.which("yt-dlp"):
            raise SystemExit("Install yt-dlp (pip install yt-dlp) or pass the video file instead.")
        r = run(["yt-dlp", "-f", "mp4/best", "-o", str(out / "media" / "ref.%(ext)s"), a.source])
        files = list((out / "media").glob("ref.*"))
        if r.returncode or not files:
            raise SystemExit("Download failed (private post, login wall, or network block). "
                             "Save the video to your phone/computer and pass the file path instead.\n"
                             + r.stderr[-600:])
        video = files[0]
    else:
        video = out / "media" / ("ref" + Path(a.source).suffix)
        shutil.copy(a.source, video)

    info = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
                           "-show_streams", str(video)]).stdout)
    dur = float(info["format"]["duration"])
    vs = next(s for s in info["streams"] if s["codec_type"] == "video")

    r = run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf",
             f"select='gt(scene,{a.scene})',showinfo", "-f", "null", "-"])
    cuts = [round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]
    shots = [0.0] + cuts + [dur]
    lengths = [round(b - a_, 3) for a_, b in zip(shots, shots[1:]) if b > a_]

    marks = [0.0, min(1.0, dur / 2)] + cuts
    step = max(1, len(marks) // a.max_frames)
    for i, t in enumerate(marks[::step][: a.max_frames]):
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t + 0.05:.2f}", "-i", str(video), "-frames:v", "1",
             "-vf", "scale=540:-2", str(out / "frames" / f"{i:02d}_{t:06.2f}s.jpg")])

    loud = run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128", "-f", "null", "-"]).stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)

    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    if has_audio:
        run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
             str(out / "media" / "audio.wav")])
        try:
            from faster_whisper import WhisperModel
            segs, _ = WhisperModel("small", compute_type="int8").transcribe(str(out / "media" / "audio.wav"))
            (out / "transcript.txt").write_text(
                "\n".join(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}" for s in segs))
        except ImportError:
            pass

    report = {
        "source": a.source, "id": rid, "duration": round(dur, 2),
        "resolution": f"{vs.get('width')}x{vs.get('height')}", "fps": vs.get("avg_frame_rate"),
        "cuts": cuts, "shot_count": len(lengths),
        "cuts_per_minute": round(len(cuts) / dur * 60, 1) if dur else 0,
        "avg_shot_seconds": round(sum(lengths) / len(lengths), 2) if lengths else dur,
        "shortest_shot": min(lengths) if lengths else None, "longest_shot": max(lengths) if lengths else None,
        "integrated_loudness_lufs": float(lufs[-1]) if lufs else None,
        "has_audio": has_audio, "transcript": (out / "transcript.txt").exists(),
        "frames_dir": str((out / "frames").relative_to(ROOT)),
    }
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nNext: Research agent reads {report['frames_dir']}/ and writes brand/references/{rid}/recipe.md")


if __name__ == "__main__":
    main()
