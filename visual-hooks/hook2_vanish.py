#!/usr/bin/env python3
"""HOOK 2: VANISH (you materialise out of your own clothes)

Opens on your empty clothes lying on the couch. Your glasses float up into
place, then your body fills in from the clothes outward with a soft glowing
edge, and you are already talking.

YOU MUST FILM (all on a TRIPOD that never moves, same light, no auto-exposure:
long-press to lock AE/AF on iPhone, HDR Video OFF):
  1. EMPTY plate, 3 s: the couch with nobody and nothing on it.
  2. CLOTHES plate, 3 s: the outfit you are wearing laid out where you sit,
     glasses resting on top.
  3. (optional) GLASSES drop, 2 s: hang the glasses on clear fishing line
     from above the frame so they sit where your face will be, then let go
     so they drop onto the clothes. No hand in shot. The drop must happen in
     the first 1.2 s of this clip. The script plays it in reverse so the
     glasses float up.
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

from common import OUT_FPS, comp, ease_in_out, iter_clip, peek, person_mask, read_clip, still, write_video


def main():
    p = argparse.ArgumentParser(description="Vanish visual hook")
    p.add_argument("--empty", required=True, help="clean plate: the empty spot, filmed as VIDEO from the tripod")
    p.add_argument("--clothes", required=True, help="your clothes laid out in the spot, filmed as VIDEO from the tripod")
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
    first, talk = peek(iter_clip(a.talking, a.talk_start, a.talk_end))

    intro = [clothes] * int(a.hold * OUT_FPS)
    base = clothes
    if a.glasses:
        g = read_clip(a.glasses)[::-1]            # reverse: the drop becomes a float up
        g = g[-int(1.2 * OUT_FPS):]               # keep the drop itself (end of the reversed clip)
        n_g = int(0.8 * OUT_FPS)
        g = [g[int(i * len(g) / n_g)] for i in range(n_g)]  # squeeze to 0.8 s
        intro += g
        base = g[-1]                              # glasses up at face height, clothes on the couch

    # where the reveal starts: centre of your body in the first talking frame
    m0 = person_mask(first, empty, a.thresh, feather=0)
    ys, xs = np.nonzero(m0 > 0.5)
    if len(xs) == 0:
        raise SystemExit("Could not find you against the empty plate. Was the tripod moved, or the light changed? "
                         "Try --thresh 18.")
    cx, cy = int(xs.mean()), int(ys.mean())
    rmax = float(np.sqrt(((xs - cx) ** 2 + (ys - cy) ** 2).max())) * 1.1
    h, w = first.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2).astype(np.float32)
    rng = np.random.default_rng(7)                # organic edge: low-frequency noise on the distance field
    noise = cv2.resize(rng.random((h // 40, w // 40)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    dist += (noise - 0.5) * rmax * 0.2

    n_rev = int(a.reveal * OUT_FPS)
    soft = rmax * 0.12

    def frames():
        yield from intro
        for i, f in enumerate(talk):
            if i >= n_rev:
                yield f
                continue
            x = (i + 1) / n_rev                   # reaches exactly 1.0 on the last reveal frame
            mask = person_mask(f, empty, a.thresh)
            r = ease_in_out(x) * (rmax + soft)
            reveal = np.clip((r - dist) / soft, 0, 1)
            edge = np.clip(1 - np.abs(r - dist) / (soft * 0.6), 0, 1) * mask * (1 - x)
            k = ease_in_out((x - 0.5) * 2)       # clothes on the couch fade out in the second half
            bg = cv2.addWeighted(base, 1 - k, f, k, 0)
            frame = comp(f, bg, mask * reveal)
            yield comp(np.full_like(frame, 255), frame, edge * 0.6)  # bright rim on the growing edge

    dur = (a.talk_end - a.talk_start) if a.talk_end is not None else None
    write_video(frames(), a.out, audio=[(a.talking, a.talk_start, len(intro) / OUT_FPS, dur)])


if __name__ == "__main__":
    main()
