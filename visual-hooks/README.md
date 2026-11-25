# Visual hooks for talking-head reels

One script per hook. Each one exports a 1080×1920, 30 fps H.264 MP4 with your audio, ready for Instagram or CapCut.

| Hook | Script | What you see |
|---|---|---|
| 1. The Orbit 360 | `hook1_orbit360.py` | The camera whips around from behind you with motion blur, eases onto your face, punches in, and you start talking |
| 2. Vanish | `hook2_vanish.py` | Your empty clothes lie on the couch. Your glasses float up, then your body fills in from the clothes outward with a glowing edge |
| 3. Sticker Peel | `hook3_sticker_peel.py` | You pop in as a die-cut sticker, then a white paper flap peels bottom to top and reveals you talking |

## Setup (once, on your computer)
```bash
# Mac
brew install ffmpeg python
# Windows
winget install ffmpeg Python.Python.3.12

pip install -r requirements.txt
```

## The rule that makes or breaks it
The code can't fake footage. Hooks 2 and 3 cut you out by comparing each frame with an empty shot of the same spot, so:
- **Tripod, every time.** If the phone moves even a few millimetres between the empty shot and the talking take, the cut-out breaks.
- **Lock exposure and focus.** On iPhone, long-press the screen until you see AE/AF LOCK. Auto-exposure shifting is the #1 reason a cut-out fails.
- **Use steady light.** Window light changing behind a cloud will break the cut-out. Use a lamp or a ring light.
- **Don't wear the same colour as the wall behind you.**

## Shot list
**Hook 1 (Orbit 360):** one continuous take. Start with the phone behind your shoulder, walk it in a half-circle around you at chest height, stop in front of you, hold 1 second, then talk. Film at 60 fps.
```bash
python hook1_orbit360.py --clip orbit.mp4 --land 2.4 --out hook1.mp4
```
`--land` is the second where the camera stops in front of you.

**Hook 2 (Vanish):** all four shots from the same tripod position.
1. `empty.mp4`: the empty couch, 3 s
2. `clothes.mp4`: your outfit laid out where you sit, glasses on top, 3 s
3. `glasses.mp4` (optional): drop the glasses from face height onto the clothes. Only your hand may enter, from the top.
4. `talk.mp4`: you, in that outfit, in that spot, talking within the first second
```bash
python hook2_vanish.py --empty empty.mp4 --clothes clothes.mp4 --glasses glasses.mp4 --talking talk.mp4 --out hook2.mp4
```

**Hook 3 (Sticker Peel):** two shots from the same tripod position: `empty.mp4` (3 s) and `talk.mp4`.
```bash
python hook3_sticker_peel.py --empty empty.mp4 --talking talk.mp4 --out hook3.mp4
```

## If something looks off
| Problem | Fix |
|---|---|
| Parts of you are missing or see-through | `--thresh 18` |
| Background blotches show around you | `--thresh 38` |
| "Could not find you against the empty plate" | The tripod moved or the light changed. Reshoot the empty plate right before the talking take. |
| The effect is too slow or too fast | Hook 1: `--ramp`. Hook 2: `--reveal`. Hook 3: `--peel` and `--intro` |
| You want to trim your talking take | `--talk-start` and `--talk-end` (hooks 2 and 3), or `--end` (hook 1) |

Add text and captions in CapCut after export. The scripts leave the frame clean so your caption style stays yours.
