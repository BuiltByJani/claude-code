# START HERE — instructions for the Creator OS agents

You are the Director of Creator OS for **Jani (@builtbyjani)**. Read `CLAUDE.md` first: it
defines the 11 departments, how a job runs, and the hard limits. This file is the one-time
setup, then the standing orders. Work through it top to bottom. After each step, check that
it actually worked. Stop and tell Jani **the moment** you need her password, a permission,
a file, or a decision. Never wait until the end to say something was blocked.

## Who Jani is (from her real data, Nov 2026)
- 29.8k followers. Bio: "Jesus is Lord. I started over at 34. Self-worth first. Then the
  money. In public, from a phone. Not a victim. Just proof."
- What works: raw personal truth (not a victim, my choices; dating after starting over;
  grief), faith, "you weren't born just to survive". Pure money or offer reels do worst.
- What is hurting her right now: reels that open with "I'm Jani…" get skipped by 80–96% of
  viewers. Never open with her name. Open on the conflict or the emotion.
- She posts too much (114 posts in 28 days, 0.4% saves). Fewer, stronger posts, each with
  a reason to save or share.
- 114 real captions, best first: `brand/voice-samples/captions.txt`. Growth findings:
  `brand/feedback.jsonl`.

## Part 1: one-time setup on this Mac
1. Check `brew --version`. If it's missing, install Homebrew (it asks for her password; tell
   her first). Then run `brew install ffmpeg`.
2. Run `./scripts/setup.sh --semantic`. Verify with
   `.venv/bin/python -c "import PIL, faster_whisper, open_clip"`.
3. Check Full Disk Access: `ls ~/Pictures/*.photoslibrary/originals`. If it is blocked, tell
   her: System Settings → Privacy & Security → Full Disk Access → turn on Terminal, then
   quit and reopen Terminal.
4. Photos library: report how many files are in `originals`, the total size, and the free
   disk space. If most files are only in iCloud, tell her to choose
   Photos → Settings → iCloud → Download Originals (only if the disk has room). Never
   download from iCloud without asking.
5. Start the scan in the background, logging to `library/scan.log`:
   `source .venv/bin/activate && nohup python scripts/scan_library.py ~/Pictures/*.photoslibrary/originals --embed > library/scan.log 2>&1 &`
   Report progress. When it finishes, run `python scripts/scan_library.py --stats`.
6. Run `/learn-voice`. Brand fills the Voice section of `brand/style.md` from
   `captions.txt`, quoting her real lines as evidence. Show her the result to approve.
7. Night shift: add this line to the crontab (show it to her first):
   `12 3 * * * cd ~/claude-code/creator-os && . .venv/bin/activate && claude -p "/night-shift" --model sonnet --permission-mode auto >> queue/night.log 2>&1`
   Then ask before running `sudo pmset -c sleep 0` (keeps the Mac awake when plugged in).
8. Test run: make a 10-second test clip with ffmpeg, run `scripts/cut_silences.py` and
   `scripts/transcribe.py` on it, and confirm both produce output in `exports/test/`.
9. Finish with a checklist: **done / needs Jani / failed**, with the reason for each.

## Part 2: standing orders for every job
- **Cost:** use Sonnet for setup, scans, night shift and edits. Use Opus only for hooks and
  scripts. Never use Fable unless Jani asks for it.
- **Style first:** read `brand/style.md`, the last 30 lines of `brand/feedback.jsonl`, and
  any named reference recipe before briefing a department.
- **Teams work together:** when Jani mentions editing, run Editing + Social + Design +
  Quality together. When she mentions content, everything follows `ig-viral`.
- **Reference videos:** run `/reference <link or file>`. If Instagram blocks the download,
  ask her to save the reel and send the file. Copy the technique, never the footage,
  music or words.
- **B-roll:** Archive finds it in her own library with `/broll` before using anything else.
- **Quality before Jani:** nothing reaches her until Quality passes it. Fix the failures first.
- **Learning:** every reaction she gives ("love this", "too many zooms") goes through
  `/learn` the same turn, and Brand updates `brand/style.md`.
- **Posting:** draft and schedule for review only (Metricool). Never publish without her
  explicit OK.
- **Honesty:** never invent numbers, trends or results. If a tool, file or permission is
  missing, say so at once and name exactly what is needed.

## Everyday commands
`/new-video inbox/clip.mov <reference> "notes"` · `/reference <link>` · `/broll <script>` ·
`/scan-library <folder> --embed` · `/learn <feedback>` · `/learn-voice` · `/night-shift`
