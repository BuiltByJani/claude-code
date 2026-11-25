#!/usr/bin/env python3
"""HOOK 3: STICKER PEEL

You pop up as a die-cut sticker (thick white outline, drop shadow), then the
scene is peeled like a sticker sheet: a white paper flap sweeps from the
bottom of the frame to the top, and you appear under it, already talking.

YOU MUST FILM (TRIPOD, never moves, exposure locked):
  1. EMPTY plate, 3 s: the spot with nobody in it.
  2. TALKING take: sit in that spot and start your line in the first second.
  Optional, for the real-hand version in the original reel: film your hand
  pinching and pulling up toward the top-right corner against a green wall
  and lay it on top in CapCut. The script already draws the paper flap, so
  the hand is a bonus, not required.

USAGE
  python hook3_sticker_peel.py --empty empty.mp4 --talking talk.mp4 --out hook3.mp4

  --intro    seconds of the die-cut sticker pop before the peel (0 = skip, default 0.7)
  --peel     seconds for the peel to cross the frame (default 1.0)
  --angle    tilt of the peel edge in degrees (default 14)
  --thresh   matte sensitivity, same as hook 2 (default 28)
"""
import argparse
import math

import cv2
import numpy as np

from common import OUT_FPS, comp, ease_in_out, person_mask, read_clip, still, write_video


def sticker_frame(person, empty, mask, t, stroke=26):
    """Person cut-out with a white die-cut border and shadow, popping in with a small overshoot.

    Only the sticker moves; the blurred background stays put.
    """
    h, w = person.shape[:2]
    hard = (mask > 0.5).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (stroke * 2 + 1, stroke * 2 + 1))
    outline = cv2.GaussianBlur(cv2.dilate(hard, k), (5, 5), 0).astype(np.float32) / 255

    color = comp(person, np.full_like(person, 255), mask)        # person on white = sticker face
    # pop: 0.85 -> 1.04 -> 1.0 with a slight rotation
    s = 0.85 + 0.19 * ease_in_out(min(1, t / 0.6)) - 0.04 * ease_in_out(max(0, (t - 0.6) / 0.4))
    rot = -4 * (1 - ease_in_out(min(1, t / 0.7)))
    ys, xs = np.nonzero(hard)
    M = cv2.getRotationMatrix2D((float(xs.mean()), float(ys.mean())), rot, s)
    color = cv2.warpAffine(color, M, (w, h), borderValue=(255, 255, 255))
    alpha = cv2.warpAffine(outline, M, (w, h)) * min(1.0, t / 0.12)
    shadow = cv2.GaussianBlur(np.roll(alpha, (22, 12), (0, 1)), (51, 51), 0) * 0.45

    bg = cv2.GaussianBlur(empty, (0, 0), 6)
    bg = cv2.addWeighted(bg, 0.75, np.full_like(bg, 235), 0.25, 0)
    frame = comp(np.zeros_like(bg), bg, shadow)
    return comp(color, frame, alpha)


def main():
    p = argparse.ArgumentParser(description="Sticker Peel visual hook")
    p.add_argument("--empty", required=True)
    p.add_argument("--talking", required=True)
    p.add_argument("--talk-start", type=float, default=0.0)
    p.add_argument("--talk-end", type=float, default=None)
    p.add_argument("--intro", type=float, default=0.7)
    p.add_argument("--peel", type=float, default=1.0)
    p.add_argument("--angle", type=float, default=14)
    p.add_argument("--thresh", type=int, default=28)
    p.add_argument("--out", default="hook3_sticker_peel.mp4")
    a = p.parse_args()

    empty = still(a.empty, at=0.5)
    talk = read_clip(a.talking, a.talk_start, a.talk_end)
    h, w = talk[0].shape[:2]
    out = []

    # 1) die-cut sticker pop (frozen first frame of you)
    if a.intro > 0:
        m = person_mask(talk[0], empty, a.thresh, feather=2)
        if m.max() < 0.5:
            raise SystemExit("Could not find you against the empty plate. Tripod moved or light changed? Try --thresh 18.")
        n = int(a.intro * OUT_FPS)
        out += [sticker_frame(talk[0], empty, m, i / n * 1.0) for i in range(n)]

    # 2) peel: edge travels bottom -> top
    th = math.radians(a.angle)
    nx, ny = math.sin(th), -math.cos(th)          # normal points "up" (toward the unpeeled part)
    tx, ty = -ny, nx                               # along the edge
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    proj = xx * nx + yy * ny                       # distance along the peel direction
    along = xx * tx + yy * ty
    a_mid, a_half = along.mean(), (along.max() - along.min()) / 2
    lo, hi = proj.min(), proj.max()
    flap_max = h * 0.11

    n_peel = int(a.peel * OUT_FPS)
    for i, f in enumerate(talk):
        if i >= n_peel:
            out.append(f)
            continue
        x = ease_in_out((i + 1) / n_peel)
        fh = flap_max * (0.3 + 0.7 * math.sin(math.pi * x))      # flap lifts, then lies flat at the top
        d = lo - fh + (hi - lo + 2 * fh) * x
        curl = fh * (1 - 0.35 * np.clip((along - a_mid) / a_half, -1, 1) ** 2)  # curved lip of the flap

        revealed = np.clip((d - proj) / 2.0, 0, 1)                   # under the edge: you
        frame = comp(f, empty, revealed)

        # soft shadow cast by the flap onto the revealed area
        shadow = np.clip(1 - (d - proj) / (fh * 0.9 + 1), 0, 1) * revealed * 0.35
        frame = comp(np.zeros_like(frame), frame, shadow)

        # the white back of the sticker
        rel = (proj - d) / np.maximum(curl, 1)
        flap = ((rel >= 0) & (rel <= 1)).astype(np.float32)
        flap = cv2.GaussianBlur(flap, (3, 3), 0)
        shade = (205 + 50 * np.clip(rel, 0, 1)).astype(np.uint8)    # darker at the fold, bright at the lip
        paper = np.dstack([shade, shade, shade])
        lip_shadow = np.clip(1 - (rel - 1) * 4, 0, 1) * (rel > 1) * 0.3  # shadow the lip casts ahead of it
        frame = comp(np.zeros_like(frame), frame, lip_shadow.astype(np.float32))
        frame = comp(paper, frame, flap)
        out.append(frame)

    start_out = len(out) - len(talk)
    write_video(out, a.out, audio=[(a.talking, a.talk_start, start_out / OUT_FPS, len(talk) / OUT_FPS)])


if __name__ == "__main__":
    main()
