#!/usr/bin/env python3
"""ig-boost check: six patterns /ig-human does not catch.

Usage: python3 -I boost_check.py clean.txt
Exit code 0 = CLEAN, 1 = at least one FLAG, 2 = could not read the file.
Standard library only. Pattern checks, not an AI detector.
"""
import re
import sys

SOURCE_HINTS = re.compile(
    r"\b(source|according to|study|survey|report|research|data from|per)\b"
    r"|\(\s*[A-Z][^)]*\d{4}\s*\)|\b(19|20)\d{2}\b",
    re.I,
)
STAT = re.compile(
    r"\b\d+(\.\d+)?\s?(%|percent)\b|\bstudies (show|say|prove)\b"
    r"|\bresearch (shows|says|proves)\b|\bscience says\b|\bstatistically\b",
    re.I,
)
UNIVERSAL = re.compile(
    r"\b(every woman|every single woman|all women|women everywhere|all of us"
    r"|everyone|everybody|every girl|all you girls|you guys|ladies)\b"
    r"(?!\s+(tells|told|says|said|keeps telling)\b)",
    re.I,
)
BUZZ = re.compile(
    r"\b(unlock(s|ed|ing)?|game[- ]?changer|game[- ]?changing|level up your life"
    r"|next level|transform(s|ed|ing|ation|ative)?|journey|dive into|delve"
    r"|revolutioni[sz]e|at scale|empower(ing|ment)?|elevate|unleash"
    r"|the future of)\b",
    re.I,
)
# Her required line: AI is the future, learn it to build your brand.
AI_LINE = re.compile(r"\bAI\b.*\bfuture\b|\bfuture\b.*\bAI\b", re.I)
CONCRETE = re.compile(
    r"\b\d+\b|\b(am|pm|monday|tuesday|wednesday|thursday|friday|saturday|sunday"
    r"|morning|night|tonight|yesterday|car|kitchen|bathroom|mirror|phone|gym"
    r"|bed|desk|coffee|jersey|said|told|texted|asked|deleted|posted)\b",
    re.I,
)
PERSONAL = re.compile(r"\b(I|I'm|I've|my|me|you|your|you're)\b", re.I)


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def is_slogan(line):
    """Short, quotable, no person in it, no concrete detail."""
    words = re.findall(r"[A-Za-z']+", line)
    if not 3 <= len(words) <= 12:
        return False
    if line.rstrip().endswith("?"):
        return False
    if re.search(r"\b(I|I'm|I've|my|me)\b", line):
        return False
    if CONCRETE.search(line):
        return False
    abstract = re.search(
        r"\b(worth|enough|power|healing|growth|becoming|magic|energy"
        r"|deserves?|purpose|strength|peace|freedom|destiny|universe|love yourself"
        r"|self[- ]?love|confidence is|your value)\b",
        line,
        re.I,
    )
    return bool(abstract)


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

    sents = sentences(text)
    flags = []

    # 1. Number with no source
    for s in sents:
        if STAT.search(s) and not SOURCE_HINTS.search(s):
            flags.append(("1 NO SOURCE", s,
                          "Name the source and year, or cut the number."))

    # 2. Quote-card slogans (more than one)
    slogans = [s for s in sents if is_slogan(s)]
    if len(slogans) > 1:
        for s in slogans:
            flags.append(("2 SLOGAN", s,
                          f"{len(slogans)} quote-card lines. Keep one, follow it "
                          "with a concrete moment."))

    # 3. "Every woman" claims
    for s in sents:
        m = UNIVERSAL.search(s)
        if m:
            flags.append(("3 EVERY WOMAN", s,
                          f'"{m.group(0)}" - talk to one woman: "you".'))

    # 4. Benefit stacking: 3+ sentences in a row opening with the same word
    def opener(s):
        w = re.findall(r"[A-Za-z']+", s.lower())
        return w[0] if w else ""
    run = 1
    for i in range(1, len(sents) + 1):
        same = i < len(sents) and opener(sents[i]) == opener(sents[i - 1]) \
            and opener(sents[i]) not in ("", "and", "but")
        if same:
            run += 1
            continue
        if run >= 3:
            block = " / ".join(sents[i - run:i])
            flags.append(("4 STACKING", block,
                          f'{run} lines open with "{opener(sents[i - 1])}". Cut by '
                          "half and add one honest limit."))
        run = 1

    # 5. Buzzwords (her AI-is-the-future line is exempt)
    for s in sents:
        if AI_LINE.search(s):
            continue
        for m in BUZZ.finditer(s):
            flags.append(("5 BUZZWORD", s,
                          f'"{m.group(0)}" - swap for a plain word.'))

    # 6. No real detail anywhere
    if sents and not any(CONCRETE.search(s) and PERSONAL.search(s) for s in sents):
        flags.append(("6 NO DETAIL", "(whole piece)",
                      "Add one specific true moment: a time, a place, a thing "
                      "said. Never invent one about Jani."))

    for tag, where, fix in flags:
        print(f"FLAG  {tag}\n      {where}\n      fix: {fix}\n")

    word_count = len(re.findall(r"\S+", text))
    if len(sents) < 3:
        print("note: very short text, check 6 and check 4 may not be meaningful.")
    print("BOOST CHECK")
    print(f"words:   {word_count}")
    print(f"flags:   {len(flags)}")
    print(f"verdict: {'CLEAN' if not flags else 'FIX FLAGS'}")
    print("(pattern checks only, not an AI detector)")
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
