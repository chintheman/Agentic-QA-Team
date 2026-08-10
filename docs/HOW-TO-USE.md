# How to use it

## The whole thing

```
/qa
```

or just type **"QA this repo"**.

That's it. If you read nothing else, that's the command.

---

# 1. Integrate — once per repo

Open the repo in Claude Code (app or CLI) and run:

```
/qa
```

It installs itself: detects your stack, writes the adapter, reads your real
tests to learn your conventions, proposes risk rules.

**You don't need to clone anything.** The session already has the repo — that
was never your step.

### Or install it everywhere at once (CLI only)

```bash
claude plugin marketplace add chintheman/Agentic-QA-Team
claude plugin install agentic-qa-team@chintheman-qa
```

Then `/qa` works in every repository you open, with nothing copied into any of
them. Check it landed:

```bash
claude plugin details agentic-qa-team
# expect: 9 agents, and Hooks (1) — the count that matters
```

**That hook is the guard.** A plugin with the agents but not the hook is the
degraded version — advice instead of gates.

| Where | Install method |
|---|---|
| **Mac/CLI** | plugin — once, works everywhere |
| **Claude app** | per repo (`/qa` self-installs) |

The app runs each session in a fresh container, so a plugin on your laptop
doesn't follow it there.

---

# 2. Use

```
/qa
```

Same command, every time. It works out what changed, picks how hard to look,
runs the gates whose tooling exists, and reports once.

### If you want something specific

| Command | When to reach for it |
|---|---|
| `/qa-oracle <ticket>` | **Before writing code** ⭐ |
| `/qa-risk` | "Is this change scary?" — cheap, ~1 min |
| `/qa-test <file>` | Harden one file's tests properly |
| `/qa-verdict` | Ship check before pushing |
| `/qa-fix <bug-id>` | Propose a fix for a confirmed bug |
| `/qa-probe "<charter>"` | Go hunting in one risky area |
| `/qa-init` | Setup only, no audit |

---

## `/qa-oracle` is the sleeper hit

Run it on a ticket **before** you write the code.

It reads the ticket and tells you what the spec doesn't determine — the
questions nobody asked. An ambiguity found now costs a two-minute conversation.
The same ambiguity found after merge costs an incident.

It's a spec review that happens to be free.

---

# 3. Repeat

Three habits, in order of value:

### 🥇 Before writing code
```
/qa-oracle <the ticket>
```

### 🥈 Before pushing
```
/qa
```

### 🥉 Automatically, on every PR

Set `ANTHROPIC_API_KEY` in **Settings → Secrets and variables → Actions**.

The workflow then comments a Confidence Report on every PR, forever, with no
prompting. Until that secret exists it skips visibly and says so — deliberately,
because a QA system that turns a PR red for being unconfigured teaches everyone
to ignore its red.

---

# Reading the output

```
VERDICT: SHIP    confidence: MEDIUM

What I checked
  Suite         115 passed, 44 skipped (28% of the suite never ran)
  Mutation      0.71 on 3 files — above the 0.60 gate
  Untested      2 of 7 behaviours have no test

What's wrong
  1. ...

What I could NOT check
  - ...
```

**Read the last section first.**

A green tick tells you nothing on its own. The gaps are the information — and if
that section is empty on a risky change, the report is rejected before you ever
see it.

### The verdicts

| Verdict | Means |
|---|---|
| **SHIP** | Evidence supports it |
| **SHIP_WITH_WATCH** | Ship, watch a named signal for an hour |
| **HOLD** | Don't |

`SHIP_WITH_WATCH` is refused automatically when the change can't be undone —
migrations, payments, anything already published. Redeploying old code doesn't
un-apply a migration or unsend an email, so "watch it" would name a response
that doesn't exist.

### Confidence caps

Confidence is limited by evidence *quality*, not by how the tests went:

- No spec available → MEDIUM at best
- Mutation gate unavailable → MEDIUM at best
- Suite red, or budget ran out → LOW

---

# Troubleshooting

**`/qa` isn't in the menu** → your session was created before it was installed.
Start a *new* session; resuming reuses the old checkout.

**It says "no mutation tool"** → install one (`pip install mutmut`,
`npm i -D @stryker-mutator/core`). Until then G2 is genuinely unavailable and
every report will say so rather than pretend.

**A gate blocks something innocent** → that's a bug in the gate, not in you.
Gates that fire on innocent commands train people to route around them. Report
it.

**Everything is blocked** → PyYAML is probably missing. The guard fails closed
when it can't read its policy: `pip install -r requirements-qa.txt`.
