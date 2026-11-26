# Creative System: design system, edit code and prompts for reels, ads and UGC

| Folder | What it is | Use it when |
|---|---|---|
| `design-system/tokens.json` | Colors, fonts, caption style, safe zones, motion, grade, audio levels | Briefing any editor, designer or AI tool |
| `edit-codes/reel.sh` | The house edit as ffmpeg commands: reframe, grade, hook text, punch-in, captions, music ducking, end card, loudness, export | Editing on your own computer |
| `edit-codes/srt2ass.py` | Turns any .srt into house-style captions with a gold keyword | Inside `reel.sh captions` |
| `prompts/PROMPTS.md` | Copy-paste prompts: edit brief, ad shot table, per-shot video prompts, UGC script, filming spec, image references, 26-hook bank, QA list | Every time you edit, make an ad or a UGC video |
| `brands/_template/` | Brand DNA, voice profile, folder layout | Copy once per brand |

## The design system in one screen

- **Palette:** ink `#1A1220` · cream `#F6F0E8` · plum `#4A1F3D` · gold `#C9A24A` (keyword) · coral `#E8553D` (CTA only) · sand `#E9DCCB`
- **Type:** Anton (hooks, ALL CAPS) · Montserrat ExtraBold (captions) · Playfair Display Italic (one emotional word) · Inter (body)
- **Captions:** 78px white, 6px ink outline, 2-4 words per card, one gold keyword per card, placed just below center
- **Rhythm:** hook by 2s → stake by 7s → new frame every 1.5-3s → payoff + one ask → loop word
- **Sound:** voice at -14 LUFS, music at -18 dB under the voice

Contrast is checked (WCAG): white on ink 18.2:1, cream on plum 11.9:1, ink on gold 7.6:1.
White on coral is 3.6:1, so coral only goes under big bold text.

## Setup on your computer (one time)

```bash
# 1. Get these files onto your Mac (they live on GitHub, not on your computer yet)
git clone -b code/sleepy-bell-rw32ni https://github.com/BuiltByJani/claude-code.git ~/claude-code
cd ~/claude-code
# 2. Mac: plain "ffmpeg" from Homebrew can't draw text or captions, so use ffmpeg-full.
#    It installs "keg-only", so you must put it first on your PATH or the old ffmpeg keeps running.
brew install ffmpeg-full
echo 'export PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
# fonts: download Anton, Montserrat, Playfair Display and Inter from fonts.google.com and install them
chmod +x creative-system/edit-codes/reel.sh
creative-system/edit-codes/reel.sh check     # says "ready" or tells you exactly what's missing
```

`reel.sh` warns you when a brand font is missing, and stops with the install command when your ffmpeg can't draw text.

## Tested (on Linux with ffmpeg 6.1, not yet on your Mac)

Every command was run on 16:9, 9:16 with no audio, 4:3 at 25fps and 720x1280 clips, with spaces and
apostrophes in the file names. Voice measured -14.0 LUFS. Output was 1080x1920 at 30fps every time.
It was written to work with the bash 3.2 and BSD tools a Mac ships with. Run `./reel.sh check` on your
Mac first. Fonts on this test machine were fallbacks, so check the look again once Anton and Montserrat are installed.
