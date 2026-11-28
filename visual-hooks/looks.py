#!/usr/bin/env python3
"""
Reference looks for Jani's Reels (Nov 28 2026). Technique only, built fresh.

  tutorial-card  Her close-up fills the frame; a rounded picture-in-picture
                 card (second take or screen recording) sits on the lower 2/3
                 with a blush/plum colour wash and a handwritten-style title.
  tool-strip     A row of 2-5 white tiles (logo + label) across the top third
                 while she talks below; optional heavy condensed keyword with
                 a soft shadow at chest height.

Every export: 1080x1920, 30 fps, H.264 + her audio, text inside the safe zone
(nothing in the top 250 px or bottom 420 px).

Examples
  python looks.py tutorial-card --main talk.mov --card screen.mov \
      --title "HOW I DO THIS..." --out card.mp4
  python looks.py tool-strip --main talk.mov --logos claude.png canva.png capcut.png \
      --labels CLAUDE CANVA CAPCUT --keyword "MY EDITING TEAM" --out strip.mp4
  Add --seconds 5 to any command for the 5-second test first.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import cv2
import numpy as np

W, H, FPS = 1080, 1920, 30
SAFE_TOP, SAFE_BOTTOM = 250, 420
# Jani's palette. Never red or orange.
WASH = {"blush": "0xE8B4B8", "plum": "0x5B2A4E", "teal": "0x2F6F6B", "gold": "0xC9A14A"}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed:\n" + r.stderr[-1500:])


def rounded_mask(w, h, radius, path):
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (radius, 0), (w - radius, h), 255, -1)
    cv2.rectangle(m, (0, radius), (w, h - radius), 255, -1)
    for cx, cy in [(radius, radius), (w - radius, radius), (radius, h - radius), (w - radius, h - radius)]:
        cv2.circle(m, (cx, cy), radius, 255, -1)
    cv2.imwrite(path, m)


def tile(logo, label, size, path):
    """White rounded tile, label on top, logo centred below (like a tool card)."""
    t = np.full((size, size, 3), 255, np.uint8)
    img = cv2.imread(logo, cv2.IMREAD_UNCHANGED)
    if img is None:
        sys.exit(f"Can't read logo: {logo}")
    box = int(size * 0.55)
    s = box / max(img.shape[:2])
    img = cv2.resize(img, (max(1, int(img.shape[1] * s)), max(1, int(img.shape[0] * s))), interpolation=cv2.INTER_AREA)
    y0 = int(size * 0.33) + (box - img.shape[0]) // 2
    x0 = (size - img.shape[1]) // 2
    roi = t[y0:y0 + img.shape[0], x0:x0 + img.shape[1]]
    if img.shape[2] == 4:
        a = img[:, :, 3:4] / 255.0
        roi[:] = (img[:, :, :3] * a + roi * (1 - a)).astype(np.uint8)
    else:
        roi[:] = img[:, :, :3]
    fs = size / 420
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
    cv2.putText(t, label, ((size - tw) // 2, int(size * 0.2)), cv2.FONT_HERSHEY_SIMPLEX, fs, (20, 20, 20), 2, cv2.LINE_AA)
    cv2.imwrite(path, t)


def esc(text):
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def font_opt(font):
    if font and os.path.isfile(font):
        return f"fontfile='{font}'"
    return f"font='{font or 'Sans'}'"


def base_in(main, seconds):
    t = ["-t", str(seconds)] if seconds else []
    return t + ["-i", main]


def fill(label):
    return (f"[{label}]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},fps={FPS},setsar=1")


def tutorial_card(a, tmp):
    # Face stays top-left, card sits offset to the lower right (like the reference).
    cw, ch = int(W * 0.72), int(H * 0.45)
    cx, cy = W - cw - 40, H - SAFE_BOTTOM - ch
    mask = os.path.join(tmp, "mask.png")
    rounded_mask(cw, ch, 48, mask)
    wash = WASH[a.wash]
    title = esc(a.title)
    t = ["-t", str(a.seconds)] if a.seconds else []
    fc = (
        f"{fill('0:v')},eq=brightness=-0.04[bg];"
        f"[1:v]scale={cw}:{ch}:force_original_aspect_ratio=increase,crop={cw}:{ch},fps={FPS},setsar=1,format=rgba,"
        f"split[c0][c1];[c1]drawbox=c={wash}@0.35:t=fill[cw];[c0][cw]blend=all_mode=softlight[cb];"
        f"[2:v]format=gray,scale={cw}:{ch}[m];[cb][m]alphamerge[card];"
        f"[bg][card]overlay={cx}:{cy}+18*max(0\\,1-t/0.25):shortest=1[v1];"
        f"[v1]drawtext={font_opt(a.font)}:text='{title}':fontsize={a.title_size}:fontcolor=white:"
        f"borderw=3:bordercolor=black@0.35:x=min(w-text_w-40\\,{cx}+20):y={cy}-text_h-36:"
        f"alpha='min(1,t/0.3)'[v]"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + base_in(a.main, a.seconds) + t + ["-stream_loop", "-1", "-i", a.card,
           "-loop", "1", "-i", mask, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
           "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", a.out]
    run(cmd)


def tool_strip(a, tmp):
    n = len(a.logos)
    if not 2 <= n <= 5:
        sys.exit("Use 2 to 5 logos.")
    labels = a.labels or [os.path.splitext(os.path.basename(p))[0].upper() for p in a.logos]
    if len(labels) != n:
        sys.exit("Give one label per logo.")
    gap = 24
    size = min(250, (W - 60 - gap * (n - 1)) // n)
    x0 = (W - (size * n + gap * (n - 1))) // 2
    y = SAFE_TOP + 20
    mask = os.path.join(tmp, "tmask.png")
    rounded_mask(size, size, 18, mask)
    ins, chain, prev = [], [f"{fill('0:v')}[s0]"], "s0"
    for i, (logo, lab) in enumerate(zip(a.logos, labels)):
        p = os.path.join(tmp, f"tile{i}.png")
        tile(logo, lab, size, p)
        ins += ["-loop", "1", "-i", p]
        k = 1 + i
        delay = 0.12 * i  # tiles pop in left to right
        chain.append(f"[{k}:v]format=rgba[t{i}];[{n + 1}:v]format=gray[m{i}];[t{i}][m{i}]alphamerge[ta{i}]")
        chain.append(f"[{prev}][ta{i}]overlay={x0 + i * (size + gap)}:{y}-30*max(0\\,1-(t-{delay})/0.2):"
                     f"enable='gte(t,{delay})':shortest=1[s{i + 1}]")
        prev = f"s{i + 1}"
    if a.keyword:
        kw = esc(a.keyword.upper())
        chain.append(f"[{prev}]drawtext={font_opt(a.font)}:text='{kw}':fontsize={a.keyword_size}:fontcolor=white:"
                     f"shadowcolor=black@0.6:shadowx=6:shadowy=6:x=(w-text_w)/2:y=h*0.52:"
                     f"enable='gte(t,{a.keyword_at})'[v]")
    else:
        chain.append(f"[{prev}]null[v]")
    t = ["-t", str(a.seconds)] if a.seconds else []
    cmd = (["ffmpeg", "-y", "-loglevel", "error"] + base_in(a.main, a.seconds) + ins + t + ["-loop", "1", "-i", mask,
           "-filter_complex", ";".join(chain), "-map", "[v]", "-map", "0:a?", "-shortest",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", a.out])
    run(cmd)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="look", required=True)
    c = sub.add_parser("tutorial-card")
    c.add_argument("--main", required=True, help="close-up talking take (her audio is kept)")
    c.add_argument("--card", required=True, help="second take or screen recording for the card")
    c.add_argument("--title", default="HOW I DO THIS...")
    c.add_argument("--title-size", type=int, default=96)
    c.add_argument("--wash", choices=WASH, default="blush")
    s = sub.add_parser("tool-strip")
    s.add_argument("--main", required=True)
    s.add_argument("--logos", nargs="+", required=True, help="2-5 logo images (PNG with transparency is best)")
    s.add_argument("--labels", nargs="+")
    s.add_argument("--keyword", help="heavy condensed word at chest height, e.g. 'MY EDITING TEAM'")
    s.add_argument("--keyword-at", type=float, default=0.6)
    s.add_argument("--keyword-size", type=int, default=110)
    for q in (c, s):
        q.add_argument("--font", help="font file or installed font name (e.g. 'Anton', 'Permanent Marker')")
        q.add_argument("--seconds", type=float, help="render only the first N seconds (5-second test)")
        q.add_argument("--out", required=True)
    a = p.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found: brew install ffmpeg")
    with tempfile.TemporaryDirectory() as tmp:
        (tutorial_card if a.look == "tutorial-card" else tool_strip)(a, tmp)
    print(f"Saved {a.out}")


if __name__ == "__main__":
    main()
