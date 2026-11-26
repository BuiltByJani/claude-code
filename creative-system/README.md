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
# Mac
brew install ffmpeg
# fonts: download Anton, Montserrat, Playfair Display and Inter from fonts.google.com and install them
chmod +x creative-system/edit-codes/reel.sh
```

`reel.sh` warns you if a font is missing instead of failing silently.

## Tested

Every `reel.sh` command was run on a test clip: reframe, blurfill, grade, loudness
(measured -14.0 LUFS), punch, hook (including `:` `%` `'` in the text), captions,
music ducking, end card, export, and the full `all` pipeline (1080x1920 H.264 + AAC).
