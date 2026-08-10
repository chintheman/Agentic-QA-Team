---
name: qa
description: QA this repository end to end and give a ship/hold verdict with evidence. Use whenever the user says "QA this", "QA the repo", "QA the build", "review this before I ship", "is this safe to ship", "check my changes", "run QA", or asks for a quality/test review of the current project. Sets itself up on first run — the user never has to install or configure anything.
---

# QA — the one command

The user wants one thing: **is this safe to ship, and what's wrong with it?**

Do the job end to end **within the bounds in step 5** — "the whole job" is not
the same as "until you run out of things to say." **Never ask a setup question.**
Never tell them to run something first. Never make them choose a mode. If
something is missing, either fix it silently or work around it and mention it
once at the end.

If the user gave an argument (a path, a ticket, "the billing change"), scope to
that. Otherwise scope it yourself, using step 2.

---

## 1. Self-install, silently

The repository is already cloned — you are running inside it. That is not a
step, and it is never the user's problem.

Check for `.qa/config.env`.

**If it exists**, QA is installed. Skip to step 2.

**If it does not**, install it now without narrating:

- If `.qa/adapters/` is missing entirely, clone
  `https://github.com/chintheman/Agentic-QA-Team` to a temp directory outside
  the repo, copy in `.claude/`, `.qa/`, `scripts/` and `agents/`, and delete the
  temp directory. **Copy the fixtures directory too** — the G3 self-test asserts
  against those files, so an install that omits them leaves the self-test
  permanently red for no real reason.
- Ensure PyYAML is present (`pip install -r requirements-qa.txt`). The guard
  fails closed without it, which blocks every tool call rather than degrading.
- Run `bash scripts/qa-init.sh` and read `.qa/INIT-REPORT.md`.
- Write `.qa/config.env` with the detected adapter. If the adapter is `custom`,
  write one from `.qa/adapters/custom.sh.template` — implement only what you can
  actually implement, and leave `qa_unimplemented` for the rest. An adapter that
  returns success from a stub turns its gate into a rubber stamp.
- Fill `.claude/skills/qa-conventions/SKILL.md` from **real test files**.
- Write `.qa/RISK-RULES.proposed.yaml`. Do **not** overwrite
  `.qa/RISK-RULES.yaml` — banding needs human sign-off.

Mention the install in one line at the end, not as a preamble.

---

## 2. Work out what to review, in this order

1. **Uncommitted changes** — `git status --porcelain`. If any, that is the target.
2. **This branch vs the default branch** — if ahead, review those commits.
3. **The last commit on the default branch** — if the tree is clean and level.
4. **Nothing changed** — say so, then audit the highest-risk module instead
   (from `.qa/RISK-RULES.yaml`, or the largest source file if unbanded) so the
   run still produces something.

State the scope in one line so they know what you looked at.

---

## 3. Band it, then match the effort

Apply `.qa/RISK-RULES.yaml` (or the `.proposed` file if that is all there is).
First matching rule wins.

| Band | Do |
|---|---|
| **low** | Run the suite. Report. Stop. |
| **medium** | Suite + vacuity + mutation on changed files. |
| **high** | The above + an oracle pass on intended behaviour, and name uncovered propositions. |
| **critical** | The above + probe the money/identity/irreversible paths for what has no test at all. |

Do not run agents that have nothing to do. If there is no browser harness, no
`flow-smith`. If there is no multi-user auth surface, no `authz-prober`.

---

## 4. Run the gates that can actually run

In cheapest-first order, skipping any whose tooling is absent:

1. **Suite** — `qa_test_all`. If it fails, that dominates everything: report it
   first and do not bury it under mutation numbers.
2. **Vacuity (G3)** — zero-assertion, mock-only, skipped, tautological tests.
3. **Mutation (G2)** — only on changed files in `mutation_paths`.
4. **fails-before/passes-after (G1)** — only when a test targets a defect.

**Missing tooling is a finding, not a blocker.** No mutation tool means the
central gate is unavailable — say so plainly and continue. Never report success
for a gate that did not run.

Count skipped tests. A suite where 28% skip proves at most 72% of itself, and
the user needs that number to read the green correctly.

---

## 5. Know when to stop

Decide the bound **before** you start, and say it in the report.

| Band | Stop after |
|---|---|
| low | the suite result |
| medium | 5 product findings, or the gates completing |
| high | 8 product findings |
| critical | 12 product findings |

Also stop when the band's `pr_budget_usd_by_band` is reached. That budget is
real even when nobody is running `scripts/qa-orchestrate.sh` — the gate exists
in the orchestrator, but the *limit* is yours to honour whether or not that code
path executes. A cap that only fires on a route nobody takes is not a cap.

When you stop early, **say so and say why**: "stopped at 8 findings (high band);
`parser/` not examined." An honest boundary is information. Continuing until you
run out of things to say is not thoroughness — it buries the first finding under
the eleventh, and the first one was the one that mattered.

**Never pad to look thorough.** Three real findings beat twelve manufactured
ones, and the twelfth costs the reader their attention for all of them.

---

## 6. One report — and the product comes first

Lead with the answer. No preamble, no method description.

**The single most important rule in this file:** your findings about the
*product* and your findings about the *QA tooling itself* are different
categories and must never share a list. A crash in the user's price index and an
uncommitted test fixture are not items 1 and 5 of the same enumeration. One is
their software being wrong. The other is scaffolding.

```
VERDICT: SHIP / SHIP_WITH_WATCH / HOLD     confidence: HIGH / MEDIUM / LOW
Scope: 3 changed files in index/ (band: critical) · stopped at gates complete

YOUR CODE                          ← the only section that gates shipping
  S1  index_engine crashes on a single-date corpus       index_engine.py:142
  S3  100% coupon yields -0.00 rather than 0.00          coupon.ts:88

QA TOOLING                         ← one line. Never a findings list.
  self-tests green · mutation 0.68 · 2 gates unavailable (no mutmut)

OPEN, NOT FIXED                    ← carried forward from .qa/bugs/
  BUG-041  S3  model card with no variants        open, 3 days

WHAT I COULD NOT CHECK
  - 44 tests skip on a clean checkout (28% of the suite never ran)
  - web/ is TypeScript; no mutation tool configured

NEXT
  <one concrete action>
```

### Severity, on product findings only

| | Meaning |
|---|---|
| **S1** | Crash, data loss, wrong money, security |
| **S2** | Core behaviour wrong for real inputs |
| **S3** | Wrong in an edge case, or user-visible but cosmetic |
| **S4** | Nit |

Unranked findings force the reader to re-derive severity themselves, which they
will do worse than you and resent doing at all.

### The hard rule about tooling

**A broken QA kit never blocks a product verdict.**

If a gate is unavailable, a fixture is missing, or a self-test is red: that is
**one line** under QA TOOLING, it caps confidence, and then you report on the
product anyway. The user asked whether their software is safe to ship. "My
scaffolding has a problem" is not an answer to that question.

If the tooling is broken so badly that you learned nothing about the product,
say exactly that in one sentence — do not fill the space with tooling findings
to look productive.

### Other rules

- **`WHAT I COULD NOT CHECK` is mandatory** on high and critical. If you cannot
  name what you did not test, you were not thinking.
- **`SHIP_WITH_WATCH` only if `ship_with_watch_available` is true**, and never
  when the change touches `rollback_unsafe_paths` — a migration or a published
  figure cannot be undone by redeploying old code, so "watch it" would name a
  response that does not exist.
- Confidence caps: no specification → MEDIUM at best. Mutation gate unavailable
  → MEDIUM at best. Suite red → LOW.
- Write for someone deciding at 5pm on a Friday. "Billing error rate above 2%
  within 30 minutes" is actionable; "keep an eye on checkout" is not.

---

## 7. Anything worth keeping goes in `.qa/bugs/`

A finding that exists only in your report dies with the conversation.

For every **S1 or S2** you do not fix in this run, write `.qa/bugs/<id>.md` with
`status: open`. That file is read by `scripts/qa-history.py` and feeds the risk
banding, and it is what lets a later run say "still open, 3 days" instead of
rediscovering it from scratch.

Set `status: fixed` when it is fixed. **A bug file with no status can never
close** — it will be counted as open forever, which is worse than never having
written it.

---

## What not to do

- Do not ask which mode, depth, or agent they want. Choose.
- Do not stop to request setup, credentials or a config file. Work around it.
- Do not report a clean verdict when a gate could not run. That is the failure
  this system exists to prevent, and it costs more trust than any missing test.
- Do not pad. Three real findings beat twelve manufactured ones.
