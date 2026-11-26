#!/usr/bin/env python3
"""srt2ass.py — turn any .srt (CapCut, Premiere, Descript, Whisper, OpusClip export) into
house-style captions: 2-4 words per card, Montserrat ExtraBold, white with ink outline,
ONE gold keyword per card (numbers, money words, emotion words), 4-frame pop-in.

    python3 srt2ass.py captions.srt captions.ass [--words 3]

Add your own power words to TIERS below or mark one in the .srt with *asterisks*.
"""
import math, re, sys, argparse

# Ranked: earlier tiers win over later tiers in the same card.
TIERS = [
    {"money", "paid", "price", "prices", "invoice", "raise", "rate", "rates", "rich", "profit", "income"},
    {"worth", "confidence", "confident", "deserve", "enough", "yours", "own", "boundaries", "boss"},
    {"stop", "never", "wrong", "mistake", "nobody", "secret", "free"},
    {"always", "first", "only", "today"},
]
NUM = re.compile(r"[$£€]?\d[\d,.]*[kKmM%x]?")
TS = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)")

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: House,Montserrat ExtraBold,78,&H00FFFFFF,&H00FFFFFF,&H0020121A,&H00000000,-1,0,0,0,100,100,0,0,1,6,0,2,60,140,740,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
GOLD = r"{\c&H4AA2C9&}"   # #C9A24A in ASS BGR order
WHITE = r"{\c&HFFFFFF&}"
POP = r"{\fscx90\fscy90\t(0,130,\fscx100\fscy100)}"


def secs(t):
    h, m, s, ms = TS.match(t.strip()).groups()
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")[:3]) / 1000


def ass_time(x):
    cs = int(round(x * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def parse_srt(text):
    for block in re.split(r"\n\s*\n", text.replace("\r", "").strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        idx = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if idx is None:
            continue
        a, b = lines[idx].split("-->")
        text = re.sub(r"<[^>]+>|\{[^}]*\}", "", " ".join(lines[idx + 1:]))
        words = text.split()
        if words:
            yield secs(a), secs(b), words


def bare(w):
    return re.sub(r"[^\w$£€%.,]", "", w).strip(".,").lower()


def pick_keyword(words):
    for i, w in enumerate(words):          # *marked* by you always wins
        if "*" in w:
            return i
    for i, w in enumerate(words):          # then numbers / money amounts
        if NUM.fullmatch(bare(w)):
            return i
    for tier in TIERS:
        for i, w in enumerate(words):
            if re.sub(r"\W", "", w).lower() in tier:
                return i
    return None


def chunk(words, n):
    """Split into balanced cards of at most n words, so no word is left alone at the end."""
    k = math.ceil(len(words) / n)
    base, extra = divmod(len(words), k)
    out, i = [], 0
    for c in range(k):
        size = base + (1 if c < extra else 0)
        out.append(words[i:i + size]); i += size
    return out


def render(words):
    k = pick_keyword(words)
    out = []
    for i, w in enumerate(words):
        w = w.replace("*", "").replace("{", "(").replace("}", ")")
        out.append(f"{GOLD}{w}{WHITE}" if i == k else w)
    return POP + " ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("srt"); ap.add_argument("ass")
    ap.add_argument("--words", type=int, default=3, help="words per caption card (2-4)")
    a = ap.parse_args()
    n = max(2, min(4, a.words))
    events = []
    for start, end, words in parse_srt(open(a.srt, encoding="utf-8-sig").read()):
        chunks = chunk(words, n)
        weights = [sum(len(w) for w in c) + len(c) for c in chunks]
        total, t = sum(weights), start
        for c, wt in zip(chunks, weights):
            s, e = t, t + (end - start) * wt / total
            t = e
            events.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},House,,0,0,0,,{render(c)}")
    if not events:
        sys.exit("no captions found in " + a.srt)
    open(a.ass, "w", encoding="utf-8").write(HEADER + "\n".join(events) + "\n")
    print(f"wrote {len(events)} caption cards -> {a.ass}")


if __name__ == "__main__":
    main()
