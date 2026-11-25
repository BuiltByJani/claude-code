---
name: "ig-boost"
description: "Extra hooks written for Jani's niche, plus six checks /ig-human does not run (stats with no source, quote-card slogans, \"every woman\" claims, benefit stacking, buzzwords, no real detail). Use with /ig-reel when picking hooks, and after /ig-human on every script, caption or carousel before Jani sees it."
---

# ig-boost

An add-on to Jani's existing pack. It does not replace `/ig-reel`, `/ig-human`
or the Chief Content Officer rules. It adds two things they do not have.

1. **Hook bank:** 16 extra hook templates, already turned toward her niche
   (self-worth, confidence, letting go, becoming, paid to be you, personal
   brand + AI). These go alongside the 26 `/ig-reel` formulas.
2. **Boost check:** six checks for the ways motivational content sounds
   written by AI that `/ig-human` misses, with a small linter.

## Rules that win every conflict

The Chief Content Officer voice and offer rules come first. In particular:

- Speak to one woman: "you". Blunt, loud, like her talking in her car in Jersey.
- Never invent a fact, number or story about Jani's life. If a hook needs her
  number (years, dollars, days), leave `{Jani's real number}` and ask her.
- Her past is context, never the subject. Never mention addiction, recovery,
  jail or prison.
- Hooks borrow a shape, never another creator's words.

## Part 1: the hook bank

Read `hooks.md` in this folder. Use it when `/ig-reel` asks for three hooks
from different formulas: one of the three may come from this bank. Score it
with `hookscore.py` the same as any other hook. The winner still has to score
50 or more under the CCO rule. A bank hook gets no free pass.

Each entry has a template, a filled example in her niche, the pillar it suits,
and how it gets ruined. Several hooks from the original pack were left out on
purpose (bait like "this will piss you off", "gatekeeping" and "dirty little
secret" conspiracy hooks, "I don't know who needs to hear this", and
duplicates of the 26 formulas). Do not add them back.

## Part 2: the boost check

Run it after `/ig-human`, on the cleaned text:

```bash
python3 -I .claude/skills/ig-boost/boost_check.py clean.txt
```

If the file is missing (for example in claude.ai), run the same six checks by
hand from the list below. Each problem gets FLAG plus the fix. Fix every FLAG
or say out loud why it stays.

1. **Number with no source.** Any percent, "9 out of 10", "most women",
   "studies show" or "research says" needs a named source and year in the same
   sentence, or it gets cut. Her own confirmed
   numbers are fine.
2. **Quote-card slogans.** Lines like "Your worth is not up for negotiation"
   that could be pasted on anyone's post. This is the biggest AI tell in her
   niche. Keep at most one per piece, and put a concrete moment right next to it
   ("like when he said you were too much and you shrank"). Her CTA lines
   ("Comment WORTH", "Follow me", "Save this") never count as slogans.
3. **"Every woman" claims.** "Every woman", "all of us", "women everywhere",
   "every other girl", "you guys", "ladies". Rewrite to "you". (Her emphatic
   "never" and "always" are voice, not a problem. So is "everyone told me".)
4. **Benefit stacking.** Three or more sentences in a row that start the same
   way ("It helps... It gives... It makes..." or "You'll... You'll...
   You'll..."). Cut the list by half and add one honest limit ("it will not fix
   this overnight"). Lines that start with "You", "Your" or "Stop" are her voice
   and are not counted.
5. **Buzzwords /ig-human misses.** transform, next level, at scale, dive into,
   "the future of". (`/ig-human` already strips unlock, journey, game-changer,
   level up, elevate, empower and the like.) Swap for plain words.
   **Exception:** her required line that AI is the future and she should learn
   it to build her brand stays. Say it plainly, in her words. Only that phrase
   is excused, not other buzzwords in the same sentence.
6. **No real detail.** Every piece needs one specific, true, physical moment:
   a time, a place, a thing said. If Jani has not given one, use the viewer's
   moment ("you, 11pm, deleting the post before anyone sees it"). Never make
   one up about Jani.

## Order of operations

1. `/ig-reel` or `/ig-caption` drafts. Hook bank optional at the hook step.
2. `/ig-human` cleans and scores.
3. `/ig-boost` check on the cleaned text. Fix every FLAG.
4. If you rewrote lines, run `/ig-human` once more.
5. Show Jani the final text with both results. Never the scores alone.

## Say this honestly

These are pattern checks, not an AI detector. A clean result means none of the
six patterns showed up. It does not mean the post will go viral or that nobody
could tell. Never say otherwise.

---
Hook templates and check ideas adapted from contentskills by contentkuba (MIT
License), https://github.com/contentkuba/contentskills, rewritten for Jani's
niche and rules.
