#!/usr/bin/env python3
"""Brand / learning loop: record the creator's feedback so every future job uses it.

  python scripts/learn.py add --verdict reject --dept editing --job reel-12 --note "too many zooms"
  python scripts/learn.py summarize      # feedback not yet folded into brand/style.md
  python scripts/learn.py mark-applied   # after Brand updates style.md
  python scripts/learn.py tail 30        # what the Director reads before each job
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "brand" / "feedback.jsonl"


def read():
    return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()] if LOG.exists() else []


def write(rows):
    LOG.write_text("".join(json.dumps(r) + "\n" for r in rows))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add")
    add.add_argument("--verdict", choices=["approve", "reject", "note"], required=True)
    add.add_argument("--dept", required=True)
    add.add_argument("--note", required=True)
    add.add_argument("--job", default="")
    sub.add_parser("summarize")
    sub.add_parser("mark-applied")
    t = sub.add_parser("tail")
    t.add_argument("n", type=int, nargs="?", default=30)
    a = ap.parse_args()

    rows = read()
    if a.cmd == "add":
        rows.append({"at": datetime.now().isoformat(timespec="seconds"), "verdict": a.verdict,
                     "dept": a.dept, "job": a.job, "note": a.note, "applied": False})
        write(rows)
        print(f"Recorded ({len(rows)} total).")
    elif a.cmd == "summarize":
        pending = [r for r in rows if not r.get("applied")]
        if not pending:
            print("Nothing new to learn.")
        for r in pending:
            print(f"- [{r['verdict']}] {r['dept']}: {r['note']}  ({r['at']}{', ' + r['job'] if r['job'] else ''})")
    elif a.cmd == "mark-applied":
        for r in rows:
            r["applied"] = True
        write(rows)
        print("All feedback marked as applied.")
    elif a.cmd == "tail":
        for r in rows[-a.n:]:
            print(f"[{r['verdict']}] {r['dept']}: {r['note']}")


if __name__ == "__main__":
    main()
