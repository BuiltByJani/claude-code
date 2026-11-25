#!/usr/bin/env python3
"""HOOK 2: VANISH (you materialise out of your own clothes)

Opens on your empty clothes lying on the couch. Your glasses float up into
place, then your body fills in from the clothes outward with a soft glowing
edge, and you are already talking.

YOU MUST FILM (all on a TRIPOD that never moves, same light, no auto-exposure:
long-press to lock AE/AF on iPhone):
  1. EMPTY plate, 3 s: the couch with nobody and nothing on it.
  2. CLOTHES plate, 3 s: the outfit you are wearing laid out where you sit,
     glasses resting on top.
  3. (optional) GLASSES drop, 2 s: hold the glasses where your face will be
     and drop them onto the clothes. Only your hand may enter the frame, and
     only from the top. The script plays it in reverse so the glasses fly up.
  4. TALKING take: sit in the same spot, wearing the outfit, and start your
     line in the first second.

USAGE
  python hook2_vanish.py --empty empty.mp4 --clothes clothes.mp4 \
      --talking talk.mp4 --glasses glasses_drop.mp4 --out hook2.mp4

  --hold     seconds on the empty clothes before anything moves (default 0.5)
  --reveal   seconds for the body to fill in (default 0.7)
  --thresh   matte sensitivity: lower it if parts of you are missing,
             raise it if background is leaking in (default 28)
"""
import argparse

import cv2
import numpy as np

from common import OUT_FPS, comp, ease_in_out, person_mask, read_clip, still, write_video


def main():
    p = argparse.ArgumentParser(description="Vanish visual hook")
    p.add_argument("--empty", required=True, help="clean plate: empty couch (video or image)")
    p.add_argument("--clothes", required=True, help="your clothes laid out on the couch (video or image)")
    p.add_argument("--talking", required=True)
    p.add_argument("--glasses", default=None, help="clip of glasses being dropped (reversed by the script)")
    p.add_argument("--talk-start", type=float, default=0.0)
    p.add_argument("--talk-end", type=float, default=None)
    p.add_argument("--hold", type=float, default=0.5)
    p.add_argument("--reveal", type=float, default=0.7)
    p.add_argument("--thresh", type=int, default=28)
    p.add_argument("--out", default="hook2_vanish.mp4")
    a = p.parse_args()

    empty = still(a.empty, at=0.5)
    clothes = still(a.clothes, at=0.5)
    talk = read_clip(a.talking, a.talk_start, a.talk_end)

    out = [clothes.copy() for _ in range(int(a.hold * OUT_FPS))]

    if a.glasses:
        g = read_clip(a.glasses)[::-1]          # reverse: glasses fly up
        g = g[: int(1.2 * OUT_FPS)] if len(g) > 1.2 * OUT_FPS else g
        g = [g[int(i * len(g) / int(0.8 * OUT_FPS))] for i in range(int(0.8 * OUT_FPS))]  # speed to 0.8 s
        out += g
        base = g[-1]                            # last frame: glasses up, clothes on couch
    else:
        base = clothes

    # where the reveal starts: centre of the body in the first talking frame
    m0 = person_mask(talk[0], empty, a.thresh, feather=0)
    ys, xs = np.nonzero(m0 > 0.5)
    if len(xs) == 0:
        raise SystemExit("Could not find you against the empty plate. Was the tripod moved, or the light changed? "
                         "Try --thresh 18.")
    cx, cy = int(xs.mean()), int(ys.mean())
    rmax = float(np.sqrt(((xs - cx) ** 2 + (ys - cy) ** 2).max())) * 1.1
    h, w = talk[0].shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2).astype(np.float32)
    # organic edge: low-frequency noise added to the distance field
    rng = np.random.default_rng(7)
    noise = cv2.resize(rng.random((h // 40, w // 40)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    dist += (noise - 0.5) * rmax * 0.2

    n_rev = int(a.reveal * OUT_FPS)
    soft = rmax * 0.12
    for i, f in enumerate(talk):
        mask = person_mask(f, empty, a.thresh)
        if i < n_rev:
            r = ease_in_out((i + 1) / n_rev) * (rmax + soft)
            reveal = np.clip((r - dist) / soft, 0, 1)
            edge = np.clip(1 - np.abs(r - dist) / (soft * 0.6), 0, 1) * mask * (1 - i / n_rev)
            # clothes lying on the couch fade out during the second half
            k = ease_in_out((i / n_rev - 0.5) * 2)
            bg = cv2.addWeighted(base, 1 - k, f, k, 0)
            frame = comp(f, bg, mask * reveal)
            glow = np.full_like(frame, 255)
            frame = comp(glow, frame, edge * 0.6)  # bright rim on the growing edge
        else:
            frame = f
        out.append(frame)

    start_out = len(out) - len(talk)
    write_video(out, a.out, audio=[(a.talking, a.talk_start, start_out / OUT_FPS, len(talk) / OUT_FPS)])


if __name__ == "__main__":
    main()
