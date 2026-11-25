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
  Film at 60 fps if you can: the motion blur looks smoother.

USAGE
  python hook1_orbit360.py --clip orbit_take.mp4 --land 2.4 --out hook1.mp4

  --land   second in the clip where the camera stops in front of you
           (scrub the clip to find it)
  --start  second where the orbit begins (default 0)
  --ramp   how long the whole orbit lasts after the ramp (default 0.9 s)
  --punch  zoom on landing, 1.0 = none (default 1.08)
"""
import argparse

import cv2
import numpy as np

from common import OUT_FPS, read_clip, write_video


def main():
    p = argparse.ArgumentParser(description="Orbit 360 visual hook")
    p.add_argument("--clip", required=True)
    p.add_argument("--land", type=float, required=True)
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--end", type=float, default=None, help="cut the talking part at this second")
    p.add_argument("--ramp", type=float, default=0.9)
    p.add_argument("--punch", type=float, default=1.08)
    p.add_argument("--out", default="hook1_orbit360.mp4")
    a = p.parse_args()
    if a.land <= a.start:
        raise SystemExit("--land must be after --start")

    # dense read of the orbit so the blur has frames to average
    dense_fps = 120
    orbit = read_clip(a.clip, a.start, a.land, fps=dense_fps)
    talk = read_clip(a.clip, a.land, a.end)

    out = []
    n_ramp = max(2, int(round(a.ramp * OUT_FPS)))
    orbit_len = len(orbit) - 1

    def src_idx(x):  # x in 0..1 of the ramp -> source frame (fast start, gentle landing)
        e = 1 - (1 - min(1.0, max(0.0, x))) ** 3
        return e * orbit_len

    for i in range(n_ramp):
        x0, x1 = i / n_ramp, (i + 1) / n_ramp
        i0, i1 = int(src_idx(x0)), int(src_idx(x1))
        idx = np.linspace(i0, max(i0, i1), num=min(12, max(1, i1 - i0 + 1))).astype(int)
        f = np.mean([orbit[j].astype(np.float32) for j in idx], axis=0).astype(np.uint8)  # motion blur
        out.append(f)

    # punch-in that settles over the first 0.5 s of the talking part
    settle = int(0.5 * OUT_FPS)
    h, w = talk[0].shape[:2]
    for i, f in enumerate(talk):
        z = a.punch - (a.punch - 1.0) * min(1.0, i / max(1, settle)) ** 0.5 if a.punch > 1 else 1.0
        if z > 1.0001:
            cw, ch = int(w / z), int(h / z)
            x, y = (w - cw) // 2, (h - ch) // 3  # bias upward, toward the face
            f = cv2.resize(f[y:y + ch, x:x + cw], (w, h), interpolation=cv2.INTER_CUBIC)
        out.append(f)

    ramp_s = n_ramp / OUT_FPS
    talk_s = len(talk) / OUT_FPS
    write_video(out, a.out, audio=[(a.clip, a.land, ramp_s, talk_s)])


if __name__ == "__main__":
    main()
