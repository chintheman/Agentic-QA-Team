#!/usr/bin/env python3
"""Normalise mutmut output to the adapter contract (.qa/adapters/README.md).

The python adapter referenced this script and it was never written, so
`qa_mutation` failed silently and the mutation gate — the design's central gate —
had never run once. That is why a QA report could claim "no evidence on faulty
math": there genuinely was none.

Reads, in order of preference:
  1. mutants/mutmut-cicd-stats.json, if `mutmut export-cicd-stats` produced it.
  2. `mutmut results` text on stdin.

Emits, on stdout:
  {"score":0.71,"killed":22,"survived":9,"timeout":1,"no_coverage":3,
   "survivors":[{"file":"...","line":0,"mutator":"...","original":"...","replacement":"..."}]}

Exits NON-ZERO and emits nothing usable when it cannot understand the input.
A normaliser that guesses produces a mutation score from nothing, and a score
from nothing is worse than no score — it is the vacuous pass the gates exist to
prevent (P5).

Verified against mutmut 3.7.0, whose `results` lines look like:

    index.references.x_slugify__mutmut_11: survived
    parser.dedupe.x_norm__mutmut_3: killed
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# mutmut 3 status vocabulary. Anything unrecognised is counted as unknown and
# reported, never quietly folded into "killed".
KILLED = {"killed"}
SURVIVED = {"survived", "bad survived"}
TIMEOUT = {"timeout", "timed out", "bad timeout"}
# Not gradeable: no test exercises the mutant, or it was never run at all.
UNCOVERED = {"no tests", "not checked", "skipped", "no coverage"}
SUSPICIOUS = {"suspicious"}

LINE_RX = re.compile(r"^\s*(?P<name>[\w.]+__mutmut_\d+)\s*:\s*(?P<status>.+?)\s*$")


def parse_results_text(text: str):
    counts = {"killed": 0, "survived": 0, "timeout": 0, "no_coverage": 0,
              "suspicious": 0, "unknown": 0}
    survivors, unknown_statuses = [], set()
    seen_any = False

    for line in text.splitlines():
        m = LINE_RX.match(line)
        if not m:
            continue
        seen_any = True
        name, status = m.group("name"), m.group("status").strip().lower()

        if status in KILLED:
            counts["killed"] += 1
        elif status in SURVIVED:
            counts["survived"] += 1
            survivors.append(name)
        elif status in TIMEOUT:
            counts["timeout"] += 1
        elif status in UNCOVERED:
            counts["no_coverage"] += 1
        elif status in SUSPICIOUS:
            counts["suspicious"] += 1
        else:
            counts["unknown"] += 1
            unknown_statuses.add(status)

    if not seen_any:
        raise ValueError(
            "no mutant lines found. Expected lines like "
            "'pkg.mod.x_func__mutmut_3: survived'. Either mutmut produced no "
            "results, or its output format changed."
        )
    if unknown_statuses:
        print(f"[mutmut_normalise] unrecognised statuses: {sorted(unknown_statuses)}",
              file=sys.stderr)
    return counts, survivors


def mutant_to_survivor(name: str) -> dict:
    """`index.references.x_slugify__mutmut_11` -> a survivor record.

    mutmut 3's text output carries no line number, mutator name or diff, so those
    fields are left empty rather than invented. unit-smith needs the *identity*
    of the survivor in order to go and look at it; a fabricated line number would
    send it to the wrong place, which is worse than an absent one.
    """
    stem = name.split("__mutmut_")[0]
    parts = stem.split(".")
    func = parts[-1]
    if func.startswith("x_"):
        func = func[2:]
    module = "/".join(parts[:-1])
    return {
        "file": f"{module}.py" if module else "",
        "line": 0,
        "mutator": "",
        "original": f"{func}()",
        "replacement": "",
        "mutant": name,
    }


def from_cicd_stats(path: Path):
    """Use mutmut's own JSON when present. Its schema is undocumented and has
    changed between releases, so every key is probed rather than assumed, and an
    unrecognised shape falls through to the text parser instead of guessing."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None

    def pick(*names):
        for n in names:
            if n in data and isinstance(data[n], int):
                return data[n]
        return None

    killed = pick("killed", "killed_mutants", "n_killed")
    survived = pick("survived", "survived_mutants", "n_survived")
    if killed is None or survived is None:
        return None
    return {
        "killed": killed,
        "survived": survived,
        "timeout": pick("timeout", "timed_out", "n_timeout") or 0,
        "no_coverage": pick("no_tests", "not_checked", "skipped") or 0,
        "suspicious": pick("suspicious") or 0,
        "unknown": 0,
    }, []


def main() -> int:
    counts = survivors = None

    stats_file = Path("mutants/mutmut-cicd-stats.json")
    if stats_file.exists():
        got = from_cicd_stats(stats_file)
        if got:
            counts, survivors = got

    if counts is None:
        text = sys.stdin.read()
        try:
            counts, survivors = parse_results_text(text)
        except ValueError as exc:
            print(f"[mutmut_normalise] FATAL: {exc}", file=sys.stderr)
            # No fallback JSON on purpose. G2 checks for an empty report and
            # reports MISCONFIGURED, which is the honest outcome.
            return 91

    # The denominator excludes uncovered mutants deliberately (D-006): a mutant
    # no test reaches is a coverage blind spot unit-smith cannot act on, not a
    # mutation failure. It is reported separately so a flattering score over
    # three covered mutants cannot pass for a well-tested file.
    gradeable = counts["killed"] + counts["survived"] + counts["timeout"]
    score = (counts["killed"] / gradeable) if gradeable else None

    out = {
        "score": round(score, 4) if score is not None else None,
        "killed": counts["killed"],
        "survived": counts["survived"],
        "timeout": counts["timeout"],
        "no_coverage": counts["no_coverage"],
        "suspicious": counts["suspicious"],
        "unknown_status": counts["unknown"],
        "gradeable_mutants": gradeable,
        "survivors": [mutant_to_survivor(s) for s in survivors[:200]],
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
