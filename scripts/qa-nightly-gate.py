#!/usr/bin/env python3
"""Decide the nightly sweep's verdict from the three sessions' execution logs.

Why this exists
---------------
The nightly sessions authenticate with the *subscription* OAuth token, which is
capped by a rolling 5-hour window shared with the owner's local Claude Code use.
When that window is exhausted mid-day the API answers 429 instantly: every
session dies in ~0.5s, $0, zero turns, and the job goes red. That is a transient
infrastructure condition, not a QA failure, and it must not read as one.

The claude-code-action writes each session's transcript to one fixed path
($RUNNER_TEMP/claude-execution-output.json) and overwrites it per session, so
the workflow copies each one out to $RUNNER_TEMP/qa-results/<session>.json
immediately after that session ends. This script reads those copies.

Verdicts
--------
  pass      every session succeeded
  deferred  every failure was a rate/usage limit AND this is a retry-eligible
            slot -> exit 0 with a warning: a later slot will pick the sweep up
  fail      anything else, or a deferred verdict on the last slot of the day
            -> exit 1 with a per-session reason

Env in:
  QA_OUTCOMES   "flake-warden=success,prober=failure,unit-smith=failure"
  QA_RESULTS    directory holding <session>.json files
  QA_SLOT       "primary" | "fallback"  (fallback may not defer)
  QA_ANNOTATE   "1" to emit ::error::/::warning:: workflow commands
  GITHUB_STEP_SUMMARY  optional, appended to when set
"""

from __future__ import annotations

import json
import os
import re
import sys

SESSIONS = ["flake-warden", "prober", "unit-smith"]

RATE_LIMIT_RE = re.compile(
    r"session limit|weekly limit|rate limit|rate_limit|usage limit|429|overloaded",
    re.IGNORECASE,
)


def classify(path: str) -> tuple[str, str]:
    """Return (kind, detail) where kind is rate_limit | error | unknown."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError as exc:
        return "unknown", f"no execution log ({exc.strerror})"

    if not raw.strip():
        return "unknown", "empty execution log"

    result: dict | None = None
    try:
        parsed = json.loads(raw)
        msgs = parsed if isinstance(parsed, list) else [parsed]
        for msg in msgs:
            if isinstance(msg, dict) and msg.get("type") == "result":
                result = msg
    except json.JSONDecodeError:
        msgs = []

    if result is None:
        # Unparseable or no result message: fall back to a text scan so a
        # limit rejection is still recognised rather than reported as a QA bug.
        if RATE_LIMIT_RE.search(raw):
            return "rate_limit", "unparsed transcript mentions a usage limit"
        return "unknown", "no result message in execution log"

    text = result.get("result") or result.get("error") or ""
    text = text if isinstance(text, str) else json.dumps(text)
    status = result.get("api_error_status")

    if status == 429 or (result.get("is_error") and RATE_LIMIT_RE.search(text)):
        return "rate_limit", text.strip() or f"HTTP {status}"
    if result.get("is_error"):
        return "error", text.strip() or "session reported is_error with no message"
    if result.get("subtype") not in (None, "success"):
        return "error", f"subtype={result.get('subtype')}"
    return "pass", ""


def main() -> int:
    outcomes = {}
    for pair in (os.environ.get("QA_OUTCOMES") or "").split(","):
        if "=" in pair:
            name, _, value = pair.partition("=")
            outcomes[name.strip()] = value.strip()

    results_dir = os.environ.get("QA_RESULTS") or os.environ.get("RUNNER_TEMP") or "/tmp"
    slot = (os.environ.get("QA_SLOT") or "primary").strip()
    annotate = os.environ.get("QA_ANNOTATE") == "1"

    missing = [s for s in SESSIONS if s not in outcomes]
    if missing:
        print(f"::error::outcome not reported for: {', '.join(missing)}")
        return 1

    failed = [s for s in SESSIONS if outcomes[s] != "success"]
    if not failed:
        summary = "All three sessions succeeded."
        print(summary)
        _write_summary(summary)
        return 0

    findings = {}
    for session in failed:
        kind, detail = classify(os.path.join(results_dir, f"{session}.json"))
        findings[session] = (kind, detail)

    rate_limited = [s for s in failed if findings[s][0] == "rate_limit"]
    genuinely_failed = [s for s in failed if findings[s][0] != "rate_limit"]

    lines = []
    for session in failed:
        kind, detail = findings[session]
        lines.append(f"| {session} | {outcomes[session]} | {kind} | {detail[:160]} |")

    header = "| session | outcome | classified as | detail |\n| --- | --- | --- | --- |"
    body = "\n".join(lines)

    if not genuinely_failed and slot != "fallback":
        message = (
            "Sweep deferred: the subscription's rolling session window was "
            "exhausted, so every session was rejected before it could run "
            "(instant 429, zero turns, $0). No QA verdict was reached and "
            "nothing needs fixing. A later slot retries the sweep."
        )
        if annotate:
            print(f"::warning::{message}")
        print(message)
        print(f"\n{header}\n{body}")
        _write_summary(f"### {message}\n\n{header}\n{body}")
        return 0

    if not genuinely_failed and slot == "fallback":
        message = (
            "Sweep did not run: the subscription's session window was exhausted "
            "at both slots, so the nightly analysis has not happened today. "
            "Raise the cap (API key for CI) or run it by hand once the window "
            "resets."
        )
        if annotate:
            print(f"::error::{message}")
        print(message)
        print(f"\n{header}\n{body}")
        _write_summary(f"### {message}\n\n{header}\n{body}")
        return 1

    print(f"{len(genuinely_failed)} session(s) failed for a non-limit reason.")
    for session in genuinely_failed:
        kind, detail = findings[session]
        line = f"{session}: {kind} — {detail}"
        print(f"::error::{line}" if annotate else line)
    for session in rate_limited:
        print(f"note: {session} was rejected by the session limit, not by a bug")
    print(f"\n{header}\n{body}")
    _write_summary(
        f"### {len(genuinely_failed)} session(s) failed\n\n{header}\n{body}"
    )
    return 1


def _write_summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    sys.exit(main())
