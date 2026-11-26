# Creator OS

An 11-department content team for Claude Code: a Director (the main session) and 11
department agents with real tools behind them — silence cutting, captions, reference-video
breakdowns, photo-library B-roll search, trial-reel variations, and a feedback loop that
writes the creator's style down so the team gets better every job.

```
Director (CLAUDE.md, main session)
├── Research    effects · fonts · transitions · sound       scripts/analyze_reference.py
├── Archive     scanner · B-roll finder · vlog maker        scripts/scan_library.py, broll_find.py
├── Writing     hooks · scripts · on-screen text (your voice)
├── Editing     cuts · captions/graphics · sound · colour   scripts/cut_silences.py, transcribe.py
├── Design      YouTube + thumbnail · carousels · stories
├── Social      captions · 5 trial reels · scheduling
├── Production  queue · night shift · your style
├── Trends · Growth · Brand (the learning loop) · Quality (checks everything first)
```

## Setup (on the computer that has the photos and footage)

```bash
brew install ffmpeg                 # macOS
./scripts/setup.sh                  # add --semantic for AI B-roll search (~2 GB)
source .venv/bin/activate
claude                              # start Claude Code inside creator-os/
```

## First run, in this order

1. **Teach it your voice.** Put 20–50 past captions in `brand/voice-samples/captions.txt`,
   then run `/learn-voice`. Without this, nothing can be "in your voice".
2. **Index your library.** Export from Photos (File → Export → Export Unmodified Original,
   or point at `~/Pictures/Photos Library.photoslibrary/originals`), then
   `/scan-library ~/Pictures/Export --embed`.
3. **Save a look.** `/reference https://www.instagram.com/reel/...` → recipe in
   `brand/references/<id>/recipe.md`.
4. **Make a video.** Drop footage in `inbox/` and run
   `/new-video inbox/take1.mov <reference link> "hook about pricing"`.
5. **Teach it.** `/learn captions too small, love the red highlight, fewer zooms`.

## Commands

| Command | What it does |
|---|---|
| `/new-video <raw> [ref] [notes]` | Full pipeline to finished reel, captions, 5 trial reels, thumbnail |
| `/reference <url or file>` | Reference video → effects / fonts / transitions / sound recipe |
| `/scan-library <folder> [--embed]` | Index photos and videos for B-roll |
| `/broll <script>` | Beat-by-beat B-roll picks from your library |
| `/learn <feedback>` | Records feedback; Brand updates `brand/style.md` |
| `/learn-voice` | Builds the Voice section from your samples |
| `/night-shift` | Processes everything in `inbox/` and writes a morning report |

## Night shift (runs while you sleep, on your Mac)

```bash
crontab -e
# 3:12 AM every day
12 3 * * * cd ~/creator-os && . .venv/bin/activate && claude -p "/night-shift" --permission-mode acceptEdits >> queue/night.log 2>&1
```
The Mac must be awake (System Settings → Battery → prevent sleep when plugged in).

## What it can't do on its own

- **Your photos live on your phone/Mac.** The library scan must run on the machine that has
  them (or an exported copy).
- **Instagram downloads** can fail on private posts or login walls; then save the reel and
  pass the file.
- **Posting** needs a connected scheduler (e.g. Metricool) and your approval every time.
- **Fonts** in captions must be installed on the machine that renders them.
