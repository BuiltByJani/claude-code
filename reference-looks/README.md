# Jani's reference looks (Nov 28 2026)

Three title looks from the reference screenshots, built fresh as transparent 1080x1920 overlays
(ProRes 4444) that drop into CapCut, DaVinci or a Claude Code edit above or under her cut-out.
The other two reference looks (Tool Strip, Tutorial Card) are built with HyperFrames.

| Look | Composition | Use it for | On camera |
| --- | --- | --- | --- |
| Reach & Pull | `ReachPull` | Dating / love, confidence | Arm straight up at 0 s, close your fist and pull down at `dropAtSeconds` |
| One-Word Truth | `OneWordTruth` | Faith, grief, one-line truths | Still, eyes can close on the hard line; layer it UNDER your cut-out so your head covers part of the word |
| Bright Title | `BrightTitle` | Lists, rules, comeback series | One clear hand gesture per point |

## Setup (once, on the Mac)

```bash
cd ~/claude-code/creator-os/reference-looks
npm install
```

## Render (change the words in a props file, one per post)

```bash
npx remotion render src/index.ts ReachPull out/pull.mov --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png --props=props/example-reachpull.json
npx remotion render src/index.ts OneWordTruth out/truth.mov --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png --props=props/example-truth.json
npx remotion render src/index.ts BrightTitle out/title.mov --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png --props=props/example-bright.json
```

Preview and tweak live: `npx remotion studio`.

Props: `durationInSeconds`, any colour: cream, blush, gold, plum, teal, lime, red, pink, blue, green,
white, black (Jani loves all colours; pick a different colour story per Reel), `topPx` >= 250 to stay
out of the top UI zone.
Fonts: Anton and Playfair Display Italic (Google Fonts, free).

Tested Nov 28: each composition renders; ProRes 4444 export has an alpha channel, 1080x1920, 30 fps.
