#!/usr/bin/env python3
"""HOOK 1: THE ORBIT 360

The camera starts BEHIND you and swings around to land on your face, then you
start talking. This script speed-ramps the orbit (fast whip, slow landing),
adds real motion blur during the whip, punches in slightly, and settles into
your talking take at normal speed with your audio.

YOU MUST FILM (code cannot fake the camera move):
  One continuous take. Start with the phone behind your shoulder, walk it
  around you in a half-circle (gimbal or steady hands, phone at chest height,
  about 1 m from you), stop in front of you, hold 1 second, then start talking.
  Film at 60 fps with HDR Video OFF.

USAGE
  python hook1_orbit360.py --clip orbit_take.mov --land 2.4 --out hook1.mp4

  --land   second in the clip where the camera stops in front of you
  --start  second where the orbit begins (default 0)
  --end    second to stop the talking part (default: end of clip)
  --ramp   how long the orbit lasts after the speed-up (default 0.9 s)
  --punch  zoom on landing, 1.0 = none (default 1.08)
"""
import argparse
from collections import deque

import cv2
import numpy as np

from common import OUT_FPS, iter_clip, write_video

SRC_FPS = 60  # orbit is sampled at 60 fps so the motion blur has frames to average


def orbit_frames(clip, start, land, ramp):
    """Stream the orbit once and emit `ramp` seconds of eased, motion-blurred frames."""
    n_src = max(2, int(round((land - start) * SRC_FPS)))
    n_out = max(2, int(round(ramp * OUT_FPS)))

    def edge(i):  # output frame i starts at this source frame (fast start, gentle landing)
        x = i / n_out
        return min(n_src, int((1 - (1 - x) ** 3) * n_src))

    bounds = [edge(i) for i in range(n_out + 1)]
    src = enumerate(iter_clip(clip, start, land, fps=SRC_FPS))
    buf, done, last = deque(), False, None
    for i in range(n_out):
        lo, hi = bounds[i], max(bounds[i + 1], bounds[i] + 1)
        while not done and (not buf or buf[-1][0] < hi - 1):
            try:
                buf.append(next(src))
                last = buf[-1][1]
            except StopIteration:
                done = True
        while buf and buf[0][0] < lo:
            buf.popleft()
        use = [f for j, f in buf if j < hi]
        if use:  # average every source frame this output frame spans = real motion blur
            yield (np.sum([u.astype(np.float32) for u in use], axis=0) / len(use)).astype(np.uint8)
        else:    # clip shorter than --land: hold the last frame
            yield last


def talk_frames(clip, land, end, punch):
    settle = int(0.5 * OUT_FPS)
    for i, f in enumerate(iter_clip(clip, land, end)):
        if punch > 1.0001:
            z = punch - (punch - 1.0) * min(1.0, i / settle) ** 0.5
            if z > 1.0001:
                h, w = f.shape[:2]
                cw, ch = int(w / z), int(h / z)
                x, y = (w - cw) // 2, (h - ch) // 3  # bias upward, toward the face
                f = cv2.resize(f[y:y + ch, x:x + cw], (w, h), interpolation=cv2.INTER_CUBIC)
        yield f


def main():
    p = argparse.ArgumentParser(description="Orbit 360 visual hook")
    p.add_argument("--clip", required=True)
    p.add_argument("--land", type=float, required=True)
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--end", type=float, default=None)
    p.add_argument("--ramp", type=float, default=0.9)
    p.add_argument("--punch", type=float, default=1.08)
    p.add_argument("--out", default="hook1_orbit360.mp4")
    a = p.parse_args()
    if a.land <= a.start:
        raise SystemExit("--land must be after --start")
    if a.end is not None and a.end <= a.land:
        raise SystemExit("--end must be after --land")
    if a.ramp <= 0:
        raise SystemExit("--ramp must be more than 0")

    n_ramp = max(2, int(round(a.ramp * OUT_FPS)))

    def frames():
        yield from orbit_frames(a.clip, a.start, a.land, a.ramp)
        yield from talk_frames(a.clip, a.land, a.end, a.punch)

    dur = (a.end - a.land) if a.end is not None else None
    write_video(frames(), a.out, audio=[(a.clip, a.land, n_ramp / OUT_FPS, dur)])


if __name__ == "__main__":
    main()
