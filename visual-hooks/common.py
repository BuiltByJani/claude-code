"""Shared helpers for the visual-hook scripts.

Every script reads clips with OpenCV, builds the frames in numpy, writes a
silent video, then uses ffmpeg to attach audio and encode an Instagram-ready
H.264 MP4 (1080x1920, 30 fps, yuv420p, faststart).
"""
import os
import shutil
import subprocess
import sys
import tempfile

import cv2
import numpy as np

OUT_W, OUT_H, OUT_FPS = 1080, 1920, 30


def need_ffmpeg():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is not installed. Mac: `brew install ffmpeg`  Windows: `winget install ffmpeg`")


def fit_9x16(frame, w=OUT_W, h=OUT_H):
    """Scale and centre-crop any frame to fill 9:16."""
    fh, fw = frame.shape[:2]
    s = max(w / fw, h / fh)
    nw, nh = int(round(fw * s)), int(round(fh * s))
    frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    x, y = (nw - w) // 2, (nh - h) // 2
    return frame[y:y + h, x:x + w]


def read_clip(path, start=0.0, end=None, fps=OUT_FPS):
    """Return a list of 9:16 frames resampled to `fps`, from `start` to `end` seconds."""
    if not os.path.exists(path):
        sys.exit(f"File not found: {path}")
    cap = cv2.VideoCapture(path)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    src = []
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    while True:
        ok, f = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if end is not None and t > end:
            break
        src.append(fit_9x16(f))
    cap.release()
    if not src:
        sys.exit(f"Could not read any frames from {path} (check --start/--end).")
    dur = len(src) / src_fps
    n = max(1, int(round(dur * fps)))
    return [src[min(len(src) - 1, int(i * src_fps / fps))] for i in range(n)]


def still(path, at=0.0):
    """One 9:16 frame from a video or an image file."""
    img = cv2.imread(path)
    if img is not None:
        return fit_9x16(img)
    return read_clip(path, start=at, end=at + 0.2)[0]


def ease_in_out(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def person_mask(frame, clean_plate, thresh=28, feather=9):
    """Difference matte: whatever differs from the empty clean plate is the person.

    Works when the camera is LOCKED OFF on a tripod and the light is constant.
    Returns a float mask 0..1 at frame size.
    """
    a = cv2.GaussianBlur(frame, (5, 5), 0).astype(np.int16)
    b = cv2.GaussianBlur(clean_plate, (5, 5), 0).astype(np.int16)
    diff = np.abs(a - b).max(axis=2).astype(np.uint8)
    _, m = cv2.threshold(diff, thresh, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=3)
    # keep the largest blob (the person), drop noise
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        m = np.where(lbl == biggest, 255, 0).astype(np.uint8)
        # fill holes
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        m = np.zeros_like(m)
        cv2.drawContours(m, cnts, -1, 255, -1)
    if feather > 0:
        m = cv2.GaussianBlur(m, (feather * 2 + 1, feather * 2 + 1), 0)
    return m.astype(np.float32) / 255.0


def comp(fg, bg, mask):
    m = mask[..., None]
    return (fg.astype(np.float32) * m + bg.astype(np.float32) * (1 - m)).astype(np.uint8)


def write_video(frames, out_path, audio=None, fps=OUT_FPS):
    """Write frames to an IG-ready MP4.

    audio: list of (file, start_sec_in_file, start_sec_in_output, duration) tuples,
    or None for silent.
    """
    need_ffmpeg()
    tmpdir = tempfile.mkdtemp()
    raw = os.path.join(tmpdir, "video.mp4")
    h, w = frames[0].shape[:2]
    vw = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for f in frames:
        vw.write(f)
    vw.release()

    total = len(frames) / fps
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", raw]
    filt, labels = [], []
    for i, (path, src_start, out_start, dur) in enumerate(audio or []):
        cmd += ["-ss", f"{src_start:.3f}", "-t", f"{dur:.3f}", "-i", path]
        d = int(out_start * 1000)
        filt.append(f"[{i + 1}:a]aresample=48000,adelay={d}|{d}[a{i}]")
        labels.append(f"[a{i}]")
    if labels:
        filt.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,apad,atrim=0:{total:.3f}[aout]")
        cmd += ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[aout]",
                "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-map", "0:v", "-an"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
            "-r", str(fps), "-movflags", "+faststart", out_path]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        # clip had no audio track: fall back to silent
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-c:v", "libx264", "-preset", "slow",
                        "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path], check=True)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"Saved {out_path}  ({total:.2f}s, {w}x{h})")
