# Copy-paste prompts: editing, ads, UGC

Every prompt below already includes the design system (`../design-system/tokens.json`).
Fill the `{braces}` and paste. Don't delete the rules blocks. They stop the tools
from drifting off-brand.

> **Voice lock.** Prompts that write spoken lines need `../brands/_template/voice.md`
> filled in from three of your own reels first. Until it exists, every script is a
> placeholder in a generic voice. Don't post one before then.

---

## 0. The house rules block (paste under ANY prompt)

```
HOUSE RULES (non-negotiable):
- Canvas 1080x1920, 9:16, 30fps. Keep text and eyes out of: top 250px, bottom 420px, right 140px.
- Hook lands in 0-2s: spoken line AND on-screen line, written separately. Motion in frame 1, never a static face.
- 0:02-0:07 is the stake: why the viewer should care. One line.
- Body: one idea per beat, and the frame changes every 1.5-3s (cut, punch-in 105-112%, or B-roll). Nothing static past 4s.
- Last 3s: pay off exactly what the hook promised, then ONE ask. The last line echoes a word from the hook so the loop replays clean.
- Length 15-45s unless told otherwise.
- Captions: Montserrat ExtraBold 78px, white, 6px #1A1220 outline, bottom edge at y=1180px, 2-4 words per card, max 2 lines, ONE gold (#C9A24A) keyword per card (a number, a money word, or an emotion). Pop-in 4 frames. No karaoke rainbow, no bouncing.
- Hook text: Anton, ALL CAPS, 96px, white with 8px #1A1220 outline, top third.
- Palette only: ink #1A1220, cream #F6F0E8, plum #4A1F3D, gold #C9A24A, coral #E8553D (CTA only, max once per frame), sand #E9DCCB.
- Grade: warm, clean, skin-first. Never orange skin.
- Audio: voice -14 LUFS, peak -1 dBTP, music ducked to -18 dB under voice, max 3 SFX per 30s.
- Hard cuts. Max 2 whip/match cuts per video. No dissolves.
- End card (optional) 1.5s, added AFTER the payoff: plum background, cream Anton CTA, gold handle. Skip it on loop reels.
- Copy the formula, never the video: no other creator's script, voice, music edit or footage.
- Brand deals: turn on the Paid Partnership label AND put #ad in the first line of the caption, plus a verbal "this is sponsored" or "ad" in the video.
- Money and results claims: only real, documented results. If a result isn't typical, say the typical result on screen ("most clients see ..."). No income guarantees, ever.
```

---

## 1. Editing a video you already shot

### 1a. Edit brief (paste into Claude, OpusClip AI Producer, Eddie AI, Higgsfield Editing Room, CapCut AI)

```
You are a senior short-form editor. Edit the attached footage into a {15/30/45}s Instagram Reel.

GOAL: {one sentence: what the viewer should feel/do}
HOOK FORMULA: {pick from section 5, e.g. "#1 Cost Confession"}
HOOK (spoken): "{line}"
HOOK (on screen, max 6 words): "{LINE}"
PAYOFF the hook promises: {what}
CTA: {comment a word / save / follow for part 2 / link in bio}

Do this, in order:
1. Cut every pause over 0.3s, every "um/so/like" filler, every restart. Keep breaths that carry emotion.
2. Open on the strongest moment, even if it's mid-sentence (Mid-Sentence Start is allowed).
3. Change the frame every 1.5-3s: alternate wide/punch-in 108%. Punch in on numbers and on the payoff word.
4. B-roll over any line describing a thing ({list available B-roll or "suggest it"}).
5. Burn captions per HOUSE RULES. Gold keyword = the number or money word.
6. Hook text 0-2.5s, Anton, top third.
7. Music: {track or "low, warm, no vocals"}, ducked under voice.
8. End: payoff, CTA, last word echoes the hook, 1.5s plum end card.

Return: the timeline as a table (timecode | shot | spoken | on-screen text | edit move), then the export.

{paste HOUSE RULES}
```

### 1b. Same edit with the code in `../edit-codes/reel.sh` (runs on your computer)

```bash
cd creative-system/edit-codes
./reel.sh all raw.mp4 final.mp4 "NOBODY TELLS YOU THIS" captions.srt
```

Step by step, if you want control:

```bash
./reel.sh reframe  raw.mp4 1.mp4                       # 9:16 crop (or: blurfill for wide shots)
./reel.sh grade    1.mp4 2.mp4                         # house grade
./reel.sh punch    2.mp4 3.mp4 4.2 5.6 1.10            # 10% punch-in from 4.2s to 5.6s
./reel.sh hook     3.mp4 4.mp4 "STOP UNDERCHARGING"    # hook text, 0-2.5s
./reel.sh captions 4.mp4 5.mp4 captions.srt            # house captions (srt from CapCut/Descript/OpusClip)
./reel.sh music    5.mp4 6.mp4 bed.mp3                 # ducked music
./reel.sh endcard  6.mp4 7.mp4 "FOLLOW FOR PART 2" "@yourhandle"   # optional, adds 1.5s after
./reel.sh loudness 7.mp4 8.mp4                         # -14 LUFS
./reel.sh export   8.mp4 final.mp4                     # IG/TikTok upload spec
```

Mark the gold keyword yourself in the .srt by wrapping it in `*asterisks*`.

### 1c. CapCut / Premiere manual settings (for a human editor)

| Setting | Value |
|---|---|
| Project | 1080x1920, 30fps |
| Caption preset | Montserrat ExtraBold, 78, white, stroke 6 #1A1220, no shadow. CapCut Y (text center) = 1140px from top, which puts the bottom edge at 1180 |
| Keyword | #C9A24A, one word per card |
| Hook text | Anton 96, ALL CAPS, stroke 8 #1A1220, top third, 0-2.5s, 4-frame fade-in |
| Punch-in | 108-110%, 6-frame ease, on numbers and payoff |
| Grade | Temp +6, Tint 0, Contrast +6, Sat +8, Shadows +4, skin check on vectorscope |
| Audio | Voice normalize -14 LUFS, music -18 dB, auto-duck on |
| Export | H.264, 1080x1920, 30fps, high bitrate, AAC 48 kHz / 192 kbps |

---

## 2. Ads (paid or brand-deal spot)

### 2a. Ad director prompt: outputs a shot table like a production board

```
You are an ad director. Build a {15/30/60}s 9:16 ad.

PRODUCT/OFFER: {what it is, price, the one result it gives}
AUDIENCE: {who, the moment they feel the problem}
ANGLE: {problem-agitate-solve | before/after | testimonial | demo | objection-flip}
HOOK FORMULA: {from section 5}
PROOF: {real number, review, or result we are allowed to show. NO invented stats.}
OFFER/CTA: {exact words, e.g. "Comment GUIDE and I'll send it"}
REFERENCES: @image1 = {face/character}, @image2 = {product}, @image3 = {location}

Structure (beats are 2.5-4.5s each, never one long take):
HOOK (0-2.5s) -> PROBLEM -> AGITATE -> TURN (product enters) -> PROOF -> OFFER -> CTA + end card.

Output a table: # | Timecode | Beat | What happens (camera, action, light) | In frame (@refs) | Spoken/VO | On-screen text.
Then, for EVERY row, a standalone video-model prompt (section 2b format).
Then 3 alternative hooks using different formulas, so we can A/B the first 2s.

{paste HOUSE RULES}
```

### 2b. Per-shot video model prompt (Veo, Kling, Sora, Seedance, Higgsfield, Runway)

```
[SHOT {n}/{total}, {duration}s, 9:16, 30fps]
Subject: @image1 ({name}): same face, hair, skin tone and outfit as the reference, no changes.
Action: {one verb-led action, e.g. "slides a laptop toward camera and taps the screen once"}.
Camera: {static | slow push-in | handheld follow | top-down}, {lens: 35mm / 50mm / 85mm}, eye level.
Setting: @image3, {time of day}, {light: soft window light from left, warm}.
Palette: ink, cream, plum and gold tones in set dressing and wardrobe. No neon, no blue cast.
Mood: {confident, calm, quietly proud}.
Continuity: matches shot {n-1}: same lighting direction, same outfit, same props position.
Avoid: extra fingers, warped text, logos other than ours, subtitles baked in, morphing face, camera shake unless asked.
Audio: {none | ambient room tone | VO added in edit}.
```

---

## 3. UGC videos (creator-style, talking to camera)

### 3a. UGC script prompt

```
Write a UGC-style {20-35}s video in my voice (use voice.md). It must feel filmed on a phone by a real person, not an ad.

PRODUCT/TOPIC: {what}
MY TRUE STORY ANGLE: {the specific thing that happened to me, a number, a date, a feeling}
FORMAT: {talking head | get-ready-with-me | car talk | desk/laptop | "story time" | green-screen over a screenshot}
HOOK FORMULA: {from section 5}

Rules:
- First line is the hook, under 12 words, said while already moving (walking in, sitting down, holding the product).
- Sounds spoken, not written: contractions, short lines, one aside, no corporate words ("elevate", "game-changer", "unlock", "journey", "seamless" are banned).
- One concrete detail every 5s (a price, a name, a time, an object).
- Show the product by second 8 at the latest, in hand, not as a pack shot.
- Honest limit: one sentence on who this is NOT for.
- End: one ask + echo a hook word.

Output: script with beat timings | B-roll list I can shoot on my phone in 15 min | on-screen text per beat | 3 hook variants.
{paste HOUSE RULES}
```

### 3b. UGC filming spec (send this to any creator you hire)

```
- Phone vertical, 4K 30fps, back camera if someone else films, front camera for selfie style.
- Window light in front of you, never behind. No ring-light reflection in eyes for "real" style.
- Lens at eye level or slightly above. Arm's length.
- Start talking BEFORE you're settled: walk in, sit down, pick up the product mid-sentence.
- Record each line 2 ways: calm and energetic. Leave 1s silence before and after each take.
- B-roll: hands using the product (3 angles), product on the counter/desk, your reaction, your screen if digital.
- Wardrobe: solid colors from the palette (cream, plum, black, sand). No logos, no fine stripes.
- Send raw files, not the edited version. We cut it to house style.
```

### 3c. AI-generated UGC / AI creator (only if you're OK disclosing it as AI)

```
[CHARACTER LOCK: use the same face every time]
Photoreal woman, {age range}, {skin tone}, {hair: texture, length, color}, {distinct feature}.
Wardrobe baseline: {cream knit / black tank}. Natural makeup, real skin texture, no plastic smoothing.
Setting: {her apartment kitchen, morning window light from left}.
Shot: phone selfie framing, arm's length, slight handheld micro-movement, eye contact with lens.
Performance: says "{hook line}" while {action}. Natural blinks, natural mouth shapes, no over-smiling.
Keep identical across shots: face, hair, wardrobe, lighting direction.
```

Turn on TikTok's "AI-generated content" label for these. Meta adds its own "AI info" label when it detects AI.
Never present an AI person as a real user, client or customer. Under the FTC endorsement rules that's
a deceptive testimonial, whatever the platform's label says. Real testimonials come from real customers only.

---

## 4. Image / reference prompts (Nano Banana Pro, GPT Image, Midjourney, Firefly)

Build references first and video second. This order is what keeps faces consistent.

| # | Asset | Prompt |
|---|---|---|
| 0 | Face lock | `Photoreal studio headshot of {character}, neutral expression, mid-gray seamless background, soft key light 45° left, black tank top, 85mm, sharp eyes, real skin texture, no retouching.` |
| 1 | Outfit base | `Same person as reference, full body, standing, {outfit in palette colors}, mid-gray seamless, even light, front view.` |
| 2 | 6-panel sheet | `Character sheet of the same person: front, 3/4 left, profile left, 3/4 right, back, close-up face. Same outfit, same light, mid-gray seamless, labeled panels.` |
| 3 | Environment plate | `Empty {location}, no people, {time of day}, warm natural light, cream and plum decor, gold accents, 9:16 vertical, eye-level 35mm.` |
| 4 | Product hero | `{Product} on {surface}, soft window light, cream background, a plum fabric fold, gold detail, shallow depth of field, 4:5.` |
| 5 | Thumbnail/cover | `Same person as reference, {expression}, looking at camera, left third of frame, clean plum background with empty space on the right for text, 9:16.` |

Save each one under `../brands/{brand}/characters/{name}/` so every later video uses the same references.

---

## 5. Hook bank: 26 formulas, written for your niche

Formulas come from the Instagram Agent Skill (MIT, Jake Schincariol). The example lines
are starters. Swap in your real numbers and story. A made-up number is a lie on camera.

| # | Formula | Your starter line (replace the braces) |
|---|---|---|
| 1 | Cost Confession | "{$X} is what undercharging my first client cost me." |
| 2 | Negative Command | "Stop saying 'just' in your emails. Say this instead." |
| 3 | Nobody Tells You | "Nobody tells you confidence comes after you send the invoice, not before." |
| 4 | The Replacement | "This one sentence replaced {X hours} of explaining my prices." |
| 5 | Time Collapse | "Raising my rates used to take me a week of nerves. Now it takes one email." |
| 6 | The Receipt | "I said no to every discount for {N} days. Here are the actual numbers." |
| 7 | Wrong Way, Right Way | "You're pricing yourself wrong, and it's not your fault." |
| 8 | Insider Leak | "I spent {N} years {in your industry}. Here's what clients never say out loud." |
| 9 | The Steal | "Steal my rate-increase email. It took me {N} tries to get right." |
| 10 | If This, Then Watch | "If you over-explain your prices, these 20 seconds fix it." |
| 11 | Numbered With A Favourite | "3 money boundaries every woman needs. Number 3 is the one nobody uses." |
| 12 | The Objection | "'I can't charge that, nobody will pay it.' Fine. Here's the version that works anyway." |
| 13 | Before And After | Show the old DM, show the new DM, then one line on what changed. |
| 14 | The Callout | "Women who freelance, this is the one you keep ignoring." |
| 15 | The Flop Record | "My first {N} launches made nothing. Here's what changed on launch {N+1}." |
| 16 | Verbatim Question | "'How do I ask for more money without sounding greedy?' I get this every week." |
| 17 | Head To Head | "Hourly versus package pricing. I ran both for {time} and it wasn't close." |
| 18 | Cold Open Demo | Open mid-action, typing the invoice: "Watch what this does." |
| 19 | The Deadline | "Prices go up {date}. Do this before then." *(only if true)* |
| 20 | Permission | "You don't need a bigger following to charge more." |
| 21 | Mid-Sentence Start | "...and that's when I realized I was the cheapest option on purpose." |
| 22 | Contrarian Flip | "Fake it till you make it? No. Price it till you believe it." |
| 23 | The Statistic | "{N}% of {group} {fact}." *(cite the source in the caption)* |
| 24 | The Reveal | "This is the new way to say no to discounts." |
| 25 | Someone Else's Result | "One client of mine doubled her rate in {time}. Here's the exact sentence." *(written permission; if it isn't typical, say so on screen)* |
| 26 | The Superlative | "The fastest confidence boost isn't a mindset. It's a price." |

Score hooks before you shoot:
Ask Claude: `/ig-reel score this hook: "your line"` (runs `hookscore.py`). Under 50 means you don't have the hook yet.

---

## 6. QA before anything is posted (the team runs this, not you)

- [ ] Hook spoken AND on screen by 2.0s; motion in frame 1
- [ ] Nothing static past 4s; frame changes every 1.5-3s
- [ ] Captions match the audio word for word; one gold keyword per card; nothing in the safe zones
- [ ] Payoff delivers what the hook promised; one CTA only; last line echoes the hook
- [ ] Voice -14 LUFS (±1), no clipping, music not fighting the voice
- [ ] Every number is real and sourced; no other creator's script, audio edit or footage
- [ ] AI people or footage labeled where the platform requires it; no AI person presented as a real customer
- [ ] Brand deal? Paid Partnership label + #ad + verbal disclosure. Results claims typical or qualified
- [ ] Sounds like you (checked against voice.md), not like a template
- [ ] Export 1080x1920, 30fps, H.264, under 4GB
