---
# Copy this file to .qa/bugs/<id>.md. Leading underscore keeps it out of the
# harvest in scripts/qa-history.py.
---
id: BUG-000
title: <one sentence, the symptom not the guess>
status: open            # open | fixed | wontfix  <-- REQUIRED
severity: S3            # S1 crash/data loss/money · S2 core behaviour · S3 edge · S4 nit
priority: P2            # business urgency — independent of severity, on purpose
component: path/to/file.py
found_by: /qa 2026-08-10
reproducibility: always | sometimes (n/10) | once
environment: local, commit abc1234
steps:
  1. <three steps or fewer — minimise before writing this up>
expected: <what should happen, citing an oracle proposition ID where one exists>
actual: <what happens>
evidence: .qa/artifacts/<id>-trace.zip
oracle_ref: I1
---

## Notes

<why it matters, what you ruled out, anything the next person would waste an
hour rediscovering>
