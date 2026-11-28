"""Shared helpers for the visual-hook scripts.

Frames are streamed: clips are decoded one frame at a time and piped straight
into a single ffmpeg encode, so a 60 s 4K take needs well under 1 GB of RAM.
Output: 1080x1920, 30 fps, H.264 yuv420p, AAC stereo 48 kHz, faststart.
"""
import itertools
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

OUT_W, OUT_H, OUT_FPS = 1080, 1920, 30


def need_ffmpeg():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("ffmpeg is not installed. Mac: `brew install ffmpeg`  Windows: `winget install ffmpeg`")


def fit_9x16(frame, w=OUT_W, h=OUT_H):
    """Scale and centre-crop any frame to fill 9:16."""
    fh, fw = frame.shape[:2]
    s = max(w / fw, h / fh)
    nw, nh = int(round(fw * s)), int(round(fh * s))
    frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    x, y = (nw - w) // 2, (nh - h) // 2
    return frame[y:y + h, x:x + w]


def iter_clip(path, start=0.0, end=None, fps=OUT_FPS):
    """Yield 9:16 frames resampled to `fps` from `start` to `end` seconds.

    Uses each decoded frame's real timestamp, so variable-frame-rate iPhone
    clips (Auto FPS / low light) stay in sync with their audio. No seeking:
    decoding from 0 is slower but always lands on the right frame.
    """
    if not os.path.exists(path):
        sys.exit(f"File not found: {path}")
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        sys.exit(f"Could not open {path}. Is it a video file?")
    frame_dur = 1 / (cap.get(cv2.CAP_PROP_FPS) or 30)
    n_out, prev, prev_t = 0, None, None
    try:
        while True:
            ok, f = cap.read()
            t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 if ok else (prev_t or 0) + frame_dur
            if ok and t < start - 1e-3:
                continue
            stop = t if end is None else min(t, end)
            while prev is not None and start + n_out / fps < stop - 1e-6:
                yield prev                        # the frame on screen at this output tick
                n_out += 1
            if not ok or (end is not None and t >= end):
                break
            prev, prev_t = fit_9x16(f), t
    finally:
        cap.release()
    if n_out == 0:
        rng = f"{start}s to {end}s" if end is not None else f"{start}s to the end"
        sys.exit(f"No frames in {path} between {rng}. Is the clip shorter than that?")


def read_clip(path, start=0.0, end=None, fps=OUT_FPS):
    """List version of iter_clip. Only for SHORT pieces (plates, a 2 s prop clip)."""
    return list(iter_clip(path, start, end, fps))


def peek(it):
    """Return (first_item, iterator_with_first_item_put_back)."""
    first = next(it)
    return first, itertools.chain([first], it)


def still(path, at=0.0):
    """One 9:16 frame from a video (preferred) or a JPG/PNG."""
    img = cv2.imread(path)
    if img is not None:
        return fit_9x16(img)
    return next(iter_clip(path, start=at, end=at + 0.5))


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
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:  # keep the largest blob (the person), fill its holes
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        m = np.where(lbl == biggest, 255, 0).astype(np.uint8)
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        m = np.zeros_like(m)
        cv2.drawContours(m, cnts, -1, 255, -1)
    if feather > 0:
        m = cv2.GaussianBlur(m, (feather * 2 + 1, feather * 2 + 1), 0)
    return m.astype(np.float32) / 255.0


def comp(fg, bg, mask):
    m = mask[..., None]
    return (fg.astype(np.float32) * m + bg.astype(np.float32) * (1 - m)).astype(np.uint8)


def has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return bool(r.stdout.strip())


def write_video(frames, out_path, audio=None, fps=OUT_FPS):
    """Stream frames straight into one ffmpeg encode (no lossy intermediate).

    frames: any iterable of 1080x1920 BGR uint8 frames.
    audio: list of (file, start_sec_in_file, start_sec_in_output, duration_or_None).
           None duration = play until the video ends.
    """
    need_ffmpeg()
    out_dir = os.path.dirname(os.path.abspath(out_path))
    if not os.path.isdir(out_dir):
        sys.exit(f"Output folder does not exist: {out_dir}")

    tracks = []
    for tr in audio or []:
        if has_audio(tr[0]):
            tracks.append(tr)
        else:
            print(f"WARNING: {tr[0]} has no audio track, so that part will be silent.")

    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
           "-s", f"{OUT_W}x{OUT_H}", "-r", str(fps), "-i", "-"]
    filt = []
    for i, (path, src_start, out_start, dur) in enumerate(tracks):
        cmd += ["-ss", f"{src_start:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + ["-i", path]
        d = int(round(out_start * 1000))
        filt.append(f"[{i + 1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={d}:all=1,apad[a{i}]")
    if tracks:
        if len(tracks) == 1:
            filt[-1] = filt[-1].replace("[a0]", "[aout]")
        else:
            filt.append("".join(f"[a{i}]" for i in range(len(tracks)))
                        + f"amix=inputs={len(tracks)}:normalize=0[aout]")
        cmd += ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[aout]",
                "-c:a", "aac", "-ac", "2", "-b:a", "192k", "-shortest"]
    else:
        cmd += ["-map", "0:v", "-an"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-movflags", "+faststart", out_path]

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    try:
        for f in frames:
            if f.shape[:2] != (OUT_H, OUT_W):
                f = fit_9x16(f)
            p.stdin.write(np.ascontiguousarray(f).tobytes())
            n += 1
    except BrokenPipeError:
        pass
    finally:
        p.stdin.close()
    if p.wait() != 0:
        sys.exit("ffmpeg failed to write the video (see the error above).")
    print(f"Saved {out_path}  ({n / fps:.2f}s, {OUT_W}x{OUT_H})")
