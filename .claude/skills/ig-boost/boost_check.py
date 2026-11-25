#!/usr/bin/env python3
"""ig-boost check: six patterns /ig-human does not catch.

Usage: python3 -I boost_check.py clean.txt
Exit code 0 = CLEAN, 1 = at least one FLAG, 2 = could not read / empty file.
Standard library only. Pattern checks, not an AI detector.
Run it AFTER /ig-human, which already strips the common slop words.
"""
import re
import sys

STAT = re.compile(
    r"\b\d+(\.\d+)?\s?(?:%|percent\b)"
    r"|\b\d+\s+(out of|in)\s+\d+\b"
    r"|\bmost (women|people|girls|of you)\b"
    r"|\b(studies|research|science|data|experts?)\s+"
    r"(show|shows|say|says|prove|proves|found)\b"
    r"|\bstatistically\b",
    re.I,
)
YEAR = re.compile(r"\b(19|20)\d{2}\b")
UNIVERSAL = re.compile(
    r"\b(every woman|every single woman|all women|women everywhere|all of us"
    r"|every other (girl|woman)|every girl|all you girls|you guys|ladies)\b",
    re.I,
)
# /ig-human's slop.json already replaces unlock, journey, elevate, empower,
# unleash, revolutionize, game-changer, level up and delve. Only the gaps here.
BUZZ = re.compile(
    r"\b(transform(s|ed|ing|ation|ative)?|next level|at scale|dive into"
    r"|the future of)\b",
    re.I,
)
AI_WORD = re.compile(r"\bAI\b")
# A real moment: a clock time, a named place, or something said or done.
MOMENT = re.compile(
    r"\b\d{1,2}(:\d{2})?\s?(am|pm)\b"
    r"|\b(car|kitchen|bathroom|mirror|gym|bed|desk|office|parking lot|shower"
    r"|jersey|target|starbucks|work|school|church|couch|front seat)\b"
    r"|\b(said|told|texted|asked|called|deleted|cried|yelled|whispered"
    r"|screamed|replied|commented|DMed)\b",
    re.I,
)
PERSONAL = re.compile(r"\b(I|I'm|I've|my|me|you|your|you're)\b", re.I)
CTA_LINE = re.compile(
    r"^\s*(comment\s+[A-Z]{2,}\b|follow me\b|save this\b|save it\b|dm me\b)",
    re.I,
)
SLOGAN_WORDS = re.compile(
    r"\b(worth|enough|power|healing|growth|becoming|deserves?|magic|energy"
    r"|purpose|strength|peace|freedom|destiny|universe|love yourself"
    r"|self[- ]?love|confidence is|your value|prize|yourself|vibe|superpower"
    r"|main character|queen|glow|shine|abundance|birthright|unstoppable)\b",
    re.I,
)
# First words that are her voice ("you", "stop"), not benefit stacking.
VOICE_OPENERS = {"you", "your", "you're", "stop", "and", "but", "i"}


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts
            if p.strip() and not p.strip().startswith("#")]


def has_named_source(s):
    """A year plus a name: a capitalised word that is not the first word."""
    s = re.sub(r"\bMoney 2027\b", "", s)
    if not YEAR.search(s):
        return False
    if re.search(r"\([^)]*[A-Z][^)]*\d{4}[^)]*\)", s):
        return True
    words = re.findall(r"[A-Za-z][A-Za-z&.']*", s)[1:]
    return any(w[0].isupper() and w not in ("I", "I'm", "I've", "AI")
               for w in words)


def is_slogan(line):
    """Short, quotable, nothing from her life, no real moment."""
    if CTA_LINE.search(line) or line.rstrip().endswith("?"):
        return False
    words = re.findall(r"[A-Za-z']+", line)
    if not 3 <= len(words) <= 12:
        return False
    if re.search(r"\b(I|I'm|I've|my|me)\b", line) or MOMENT.search(line):
        return False
    return bool(SLOGAN_WORDS.search(line))


def first_word(s):
    w = re.findall(r"[A-Za-z']+", s.lower())
    return w[0] if w else ""


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip())
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            text = fh.read()
    except OSError as err:
        print(f"Could not read {sys.argv[1]}: {err}")
        return 2
    if not text.strip():
        print("The file is empty. Nothing to check.")
        return 2

    sents = sentences(text)
    flags = []

    # 1. Number or stat with no named source
    for s in sents:
        if STAT.search(s) and not has_named_source(s):
            flags.append(("1 NO SOURCE", s,
                          "Name the source and year, or cut the claim."))

    # 2. Quote-card slogans: more than one, or one with no moment beside it
    slog = [i for i, s in enumerate(sents) if is_slogan(s)]
    if len(slog) > 1:
        for i in slog:
            flags.append(("2 SLOGAN", sents[i],
                          f"{len(slog)} quote-card lines. Keep one."))
    elif slog and len(sents) >= 3:
        i = slog[0]
        beside = sents[max(i - 1, 0):i] + sents[i + 1:i + 2]
        if not any(MOMENT.search(b) for b in beside):
            flags.append(("2 SLOGAN", sents[i],
                          "Put a concrete moment right next to it."))

    # 3. "Every woman" claims
    for s in sents:
        m = UNIVERSAL.search(s)
        if m:
            flags.append(("3 EVERY WOMAN", s,
                          f'"{m.group(0)}" - talk to one woman: "you".'))

    # 4. Benefit stacking: 3+ lines in a row with the same first word
    run = 1
    for i in range(1, len(sents) + 1):
        if i < len(sents):
            w = first_word(sents[i])
            if w and w not in VOICE_OPENERS and w == first_word(sents[i - 1]):
                run += 1
                continue
        if run >= 3:
            flags.append(("4 STACKING", " / ".join(sents[i - run:i]),
                          f"{run} lines open the same way. Cut by half and "
                          "add one honest limit."))
        run = 1

    # 5. Buzzwords. Only "the future of" is excused, and only next to "AI".
    for i, s in enumerate(sents):
        near_ai = AI_WORD.search(s) or (i > 0 and AI_WORD.search(sents[i - 1]))
        for m in BUZZ.finditer(s):
            if m.group(0).lower() == "the future of" and near_ai:
                continue
            flags.append(("5 BUZZWORD", s,
                          f'"{m.group(0)}" - swap for a plain word.'))

    # 6. No real moment anywhere
    if not any(MOMENT.search(s) and PERSONAL.search(s) for s in sents):
        flags.append(("6 NO DETAIL", "(whole piece)",
                      "Add one specific true moment: a time, a place, a "
                      "thing said. Never invent one about Jani."))

    for tag, where, fix in flags:
        print(f"FLAG  {tag}\n      {where}\n      fix: {fix}\n")

    if len(sents) < 3:
        print("note: very short text, checks 2, 4 and 6 may not mean much.")
    words = len(re.findall(r"\S+", text))
    print("BOOST CHECK")
    print(f"words:   {words}")
    print(f"flags:   {len(flags)}")
    print(f"verdict: {'CLEAN' if not flags else 'FIX FLAGS'}")
    print("(pattern checks only, not an AI detector)")
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
