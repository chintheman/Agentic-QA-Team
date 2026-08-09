# Agentic QA Team

A team of Claude Code subagents that generates tests, executes them, hunts bugs,
proposes fixes, and issues a shipping verdict — built to the v1.1 build
specification.

**Mission:** answer one question, per change, with evidence — *is it safe to ship
this?*

Not optimised for coverage percentage, test count, or bug count. Optimised for
**calibrated shipping confidence**. The primary deliverable is a per-PR
Confidence Report: a risk-scored verdict, the evidence behind it, and an explicit
statement of what was **not** tested.

> A report saying "MEDIUM, these three paths are untested, here's why" is a
> success. A green checkmark with no reasoning is a failure even when the code
> is fine.

---

## Using it

Open any repository in Claude Code and say:

```
/qa
```

or just *"QA this repo"*.

That is the whole interface. It works out what changed, installs itself if this
is the first run, picks the depth from the risk, runs the gates whose tooling
exists, and gives you one verdict with the gaps named.

There is no setup step. The session already has the repository cloned — that was
never your job.

### 👉 Installing it? Read **[docs/INSTALL.md](docs/INSTALL.md)** first

It picks the right steps for your setup in one table — terminal, Claude app, CI,
or just trying it. **No API key is needed** unless you want it to review pull
requests automatically.

*Agents installing this for someone: `docs/INSTALL.md` has a section written for
you. Follow one scenario; do not improvise a different install.*

📖 **[How it works](docs/HOW-IT-WORKS.md)** — the design, in plain language
🚀 **[How to use it](docs/HOW-TO-USE.md)** — integrate, use, repeat

Everything below is detail for when you want to look under it.

---

## Status: this is the kit, not an instrumented repository

This repository was empty at Phase 0 — no commits, no source, no stack. So the
system is built as a **stack-agnostic, installable kit**: everything
stack-specific sits behind the adapter contract in `.qa/adapters/`.

| Phase | State |
|---|---|
| 0 — recon and capability probe | **complete.** §11 mechanisms verified empirically against CLI 2.1.226; findings in `.qa/PROFILE.md` |
| 1 — gates, no agents | **complete.** G1–G8 built, and self-tested: `bash .qa/selftest/run.sh` |
| 2–5 — the agent roster | **built, acceptance pending a real codebase.** Mutation lift and human-acceptance bars cannot be measured without one |
| 6 — calibration | wired; needs production data |

Two questions still need a human, and neither was guessed: see
`.qa/PROFILE.md` §6.

## Install into a target repository

### Recommended: install it as a plugin, once

```bash
claude plugin marketplace add chintheman/Agentic-QA-Team
claude plugin install agentic-qa-team@chintheman-qa
```

`/qa-init` and the rest are then available in **every** repository, with no
files copied anywhere. Verify with `claude plugin details agentic-qa-team` —
it should report 9 agents, 14 skills and 1 hook.

The hook matters: it is the G5 guard. A plugin that shipped the agents without
it would be the degraded mode this design exists to avoid — advice instead of
gates.

### Alternative: copy it into one repository

```bash
cp -r .claude .qa scripts .github/workflows <target-repo>/
```

Use this when you want the gates, workflows and `.qa/` artifacts committed
alongside the code they judge. Then open that repo in Claude Code and run:

```
/qa-init
```

That reads the repository, picks or writes a stack adapter, fills in the
`qa-conventions` skill from real test files, proposes risk rules, re-runs the
gate self-tests against your stack, and reports what works, what is blocked,
and what still needs a human.

It **proposes rather than imposes**: risk banding lands in
`.qa/RISK-RULES.proposed.yaml` for review, because Phase 0 requires human
sign-off before banding governs anything.

<details>
<summary>Manual equivalent, if you would rather do it by hand</summary>

```bash
.qa/adapters/detect.sh                    # pick or write an adapter
.qa/probe/capability-probe.sh --live      # re-verify §11 on your CLI
python3 scripts/qa-history.py             # build history.json from real history
bash .qa/selftest/run.sh                  # prove the gates work on your stack
```

Then fill in `.claude/skills/qa-conventions/SKILL.md` and the placeholder globs
in the risk rules, and have a human sign off on the banding.
</details>

## The team

| Agent | Owns the question |
|---|---|
| `risk-scout` | What could this break, and how hard should we look? |
| `spec-oracle` | What is this code *supposed* to do? |
| `unit-smith` | Unit/integration tests that kill mutants |
| `release-marshal` | Ship or don't — with evidence |
| `patch-smith` | Minimal fix that turns a red test green |
| `flake-warden` | Which failures are real and which are noise? |
| `flow-smith` | Browser-level tests of real journeys |
| `prober` | What breaks that nobody wrote a test for? |
| `authz-prober` | Can user A reach user B's data? |

## The gates

Non-negotiable and enforced in code. An agent can talk past a prompt instruction;
it cannot talk past a script that exits non-zero.

| Gate | Enforces |
|---|---|
| **G1** | fails-before / passes-after, **three-state** — a collection error is INCONCLUSIVE, never a pass |
| **G2** | mutation score on changed files — scoped, wall-clock capped, run once |
| **G3** | vacuity — no assertion, mock-only, skipped, or tautological tests |
| **G4** | no snapshot laundering |
| **G5** | separation of duties (the P4 table) |
| **G6** | a **running** budget checked *between* agents |
| **G7** | oracle and marshal completeness |
| **G8** | route coverage against the authz matrix |

Coverage is reported. **Coverage is never a gate** — call the code, assert
nothing, get 100%.

## Local commands

| Command | Does |
|---|---|
| **`/qa`** | **Start here — the only one most people need.** Works out what changed, installs itself if needed, runs what's affordable, gives one verdict. Also triggers on "QA this repo" in plain language. |
| `/qa-init` | Setup only, without running an audit. `/qa` does this for you on first run. |
| `/qa-risk` | Band uncommitted changes, print routing |
| `/qa-oracle <issue>` | Oracle file from a ticket — **run before writing the code** |
| `/qa-test <path>` | Full mutation loop on one file |
| `/qa-flow "<journey>"` | Plan + generate an e2e test |
| `/qa-probe "<charter>"` | One exploratory session |
| `/qa-fix <bug-id>` | Propose a fix for a confirmed bug |
| `/qa-verdict` | Confidence report before you push |

`/qa-oracle` before implementation is the highest-value habit here: it is a spec
review that catches ambiguity while it is still cheap.

## Notable findings from Phase 0

Verified against the installed CLI, and they changed the design:

- **Per-agent `hooks:` frontmatter does not work** on 2.1.226. The spec's sample
  agent (§10) is not runnable as written. Enforcement moved to settings-level
  hooks, which *do* intercept subagent tool calls.
- **The `PreToolUse` payload carries `agent_type`** — contradicting §11's
  assumption. That allowed one agent-aware guard instead of nine per-agent CI
  jobs. It fails closed: an unknown agent gets no write or shell access.
- **`--allowedTools` is a permission allowlist, not a tool-surface restriction.**
  It is effective in headless mode only. `--tools` and `--disallowedTools`
  restrict unconditionally.
- **The spec's budget numbers contradict each other** — §5 caps a PR at $8 while
  §13 estimates a critical PR at $25–50. Budgets are now band-scaled.

All deviations and their reasoning: `.qa/DECISIONS.md`.

## Known limitations

Stated plainly, per §17:

- **Test generation from code alone is a regression freezer, not a correctness
  check.** The oracle split mitigates this; it does not eliminate it. **The
  system's ceiling is set by your ticket quality**, which no prompt can fix.
- **Reward hacking scales with codebase size and search length.** The gates
  matter more as the repo grows, not less. Audit transcripts periodically.
- **E2E flake is a permanent tax.** The healer reduces it; nothing removes it.
- **The system cannot test what has no observable outcome.**
- **Two runs produce different tests.** The gates make the *result* trustworthy,
  not the process reproducible. Do not promise reproducibility.
- **Agent output is always a proposal.** A Confidence Report is an input to a
  human decision, not a substitute for one.
