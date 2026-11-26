#!/usr/bin/env python3
"""Editing / Captions: transcribe with word timestamps -> .srt, word-level .json, and a styled .ass.

Usage:
  python scripts/transcribe.py exports/job1/01_cut.mp4 [--model small] [--words-per-line 3]
         [--font "Montserrat ExtraBold"] [--size 78] [--color FFFFFF] [--highlight FF2D2D] [--margin-v 620]
Burn in:  ffmpeg -i in.mp4 -vf "ass=in.ass" -c:a copy out.mp4
"""
import argparse
import json
from pathlib import Path


def ts_srt(t):
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h:02}:{m:02}:{t % 60:06.3f}".replace(".", ",")


def ts_ass(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02}:{t % 60:05.2f}"


def bgr(hex_rgb):
    return f"&H00{hex_rgb[4:6]}{hex_rgb[2:4]}{hex_rgb[0:2]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--model", default="small")
    ap.add_argument("--words-per-line", type=int, default=3)
    ap.add_argument("--font", default="Montserrat ExtraBold")
    ap.add_argument("--size", type=int, default=78)
    ap.add_argument("--color", default="FFFFFF")
    ap.add_argument("--highlight", default="FF2D2D")
    ap.add_argument("--margin-v", type=int, default=620, help="px from bottom; keeps captions above IG UI")
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("Install: pip install faster-whisper")

    model = WhisperModel(a.model, compute_type="int8")
    segments, info = model.transcribe(a.src, word_timestamps=True, vad_filter=True)
    words = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
             for s in segments for w in (s.words or [])]
    base = Path(a.src).with_suffix("")
    Path(f"{base}.words.json").write_text(json.dumps({"language": info.language, "words": words}, indent=2))

    lines = [words[i:i + a.words_per_line] for i in range(0, len(words), a.words_per_line)]
    with open(f"{base}.srt", "w") as f:
        for n, ln in enumerate(lines, 1):
            f.write(f"{n}\n{ts_srt(ln[0]['start'])} --> {ts_srt(ln[-1]['end'])}\n{' '.join(w['word'] for w in ln)}\n\n")

    # Word-by-word highlight: one event per word, current word in highlight colour.
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Cap,{a.font},{a.size},{bgr(a.color)},&H00000000,&H64000000,1,4,0,2,80,80,{a.margin_v}

[Events]
Format: Layer, Start, End, Style, Text
"""
    ev = []
    for ln in lines:
        for i, w in enumerate(ln):
            end = ln[i + 1]["start"] if i + 1 < len(ln) else w["end"]
            txt = " ".join(
                (f"{{\\c{bgr(a.highlight)}}}{x['word']}{{\\c{bgr(a.color)}}}" if j == i else x["word"])
                for j, x in enumerate(ln))
            ev.append(f"Dialogue: 0,{ts_ass(w['start'])},{ts_ass(end)},Cap,{txt}")
    Path(f"{base}.ass").write_text(head + "\n".join(ev) + "\n")
    print(f"{len(words)} words -> {base}.srt, {base}.ass, {base}.words.json")


if __name__ == "__main__":
    main()
