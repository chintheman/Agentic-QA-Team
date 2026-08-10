# How it works

## The core idea

**Nine specialists. Each blind to something on purpose.**

Not one AI doing everything. That separation *is* the design — remove it and you
get a confident assistant that agrees with your bugs.

---

## The four that matter

| Agent | Its one question |
|---|---|
| 🔍 **risk-scout** | How hard should we look at this change? |
| 📖 **spec-oracle** | What is this code *supposed* to do? |
| 🔨 **unit-smith** | Do the tests actually prove that? |
| ⚖️ **release-marshal** | Ship or don't — with evidence |

### The other five, when they're useful

**patch-smith** proposes fixes · **flake-warden** kills flaky tests ·
**prober** explores what nobody tested · **flow-smith** browser journeys ·
**authz-prober** can user A reach user B's data

---

## The one clever bit

**`spec-oracle` is never allowed to read your code.**

That sounds broken — as though the system is reviewing your work without looking
at it. It isn't. This is the most common misreading of the design, so it is
worth being precise.

### Exactly one of the nine agents is blind

| Agent | Reads your code? |
|---|---|
| `spec-oracle` | **no** |
| `unit-smith` | yes |
| `patch-smith` | yes |
| `risk-scout` | yes — the diff |
| the mutation gate | yes — it *edits* your code and reruns the suite |

Everything that evaluates anything has full sight. What is blind is only the
**standard being measured against**.

### It's an exam, not a review

Think of marking a test paper.

**The person writing the answer key must not see the student's answers.** If they
do, the answer key quietly becomes "whatever the student wrote," and marking
becomes a formality that can never fail anyone.

**The person marking the paper sees everything.**

- `spec-oracle` writes the answer key — from your ticket, README, `docs/`, the
  API schema. It never judges, scores or approves anything.
- `unit-smith` marks the paper — and it can see every line.

### Why the separation is what makes it rigorous

An LLM that reads your implementation writes tests that *agree* with your
implementation, bugs included. You end up with a green suite that has quietly
certified the defect. Measured: assertions generated from requirements match the
*intended* behaviour at macro-F1 0.82, but match the actual buggy behaviour at
0.75. Show the model the code and it converges on the code.

If a single agent both defines "correct" and checks "correct," those two
collapse into each other and you have built a mirror. A mirror cannot disagree
with you, and disagreement is the only way a test ever finds anything.

> The oracle is blind so it can say what *should* happen.
> Everything else has full sight, so it can say what *does*.
> **The gap between them is the entire product.**

### The real limitation, which is a different one

Blind means the oracle knows only what you wrote down. **A vague ticket produces
a vague answer key**, and thin propositions produce weak tests. That ceiling is
real and no prompt removes it — it is why `/qa-oracle` is worth running on a
ticket *before* the code exists, while ambiguity is still cheap to fix.

### Enforced, not requested

This is a hook, not an instruction in a prompt. It covers `Read`, `Grep`,
`Glob`, `WebFetch` and `Bash`, because blocking `Read` alone leaves four ways
around it — including fetching your own PR diff from a URL.

The deny-list carries both file extensions **and** directory names. Extensions
catch a repo laid out in a way the list has never seen; directories catch `Grep`
and `Glob` arguments, which name folders rather than files. An earlier version
had only directories and failed open in any repo without a `src/` — silently,
while the report still claimed blindness.

---

## The gates

**Scripts, not opinions.** An agent can talk its way past an instruction in a
prompt. It cannot talk past a script that exits non-zero.

| Gate | Catches |
|---|---|
| **G1** | A "regression test" that passed before the fix too |
| **G2** | Tests that run the code but assert nothing meaningful |
| **G3** | Tests with no assertions, mock-only assertions, or `skip` |
| **G4** | Quietly re-recording a snapshot instead of fixing the bug |
| **G5** | Agents doing each other's jobs |
| **G6** | A single PR quietly costing $50 in tokens |
| **G7** | A report that hides what it didn't check |
| **G8** | A new route with no permission test |

### Coverage is deliberately *not* a gate

Call every line, assert nothing → 100% coverage, zero evidence. Coverage is
trivially gameable, so it's reported and never gated.

---

## G2 in plain English

**It breaks your code on purpose.**

Changes `>` to `>=`. Flips `+` to `-`. Deletes a line. Then reruns your tests.

- Tests fail → good. That test is real.
- Tests still pass → **that test proves nothing.**

Each surviving mutant is a concrete, specific statement that some behaviour is
unasserted. They're fed back to `unit-smith` *as the prompt* — not filed in a
report for a human to ignore.

That loop is where the value is. Without it you get high-coverage,
low-assertion tests, which is the single most common failure in LLM test
generation.

---

## Separation of duties

The failure being prevented:

> Agent writes test → test fails → *the same agent* loosens the assertion until
> it passes → everyone celebrates

So `patch-smith` **physically cannot edit a test file.** Not "is told not to" —
blocked at the tool layer, and the attempt is logged.

If it believes a test is wrong, it must file a dispute citing the specific
oracle proposition it thinks the test misencodes, and stop. That routes to
`unit-smith`, the only agent allowed to touch tests.

| Role | May write | May not write |
|---|---|---|
| Test authors | tests | any source file |
| Fixer | source | any test file |
| Analysts | their own `.qa/` folder | source, tests |
| Marshal | reports | everything else |

---

## What comes out

A **Confidence Report** per change:

```
VERDICT: SHIP / SHIP_WITH_WATCH / HOLD    confidence: HIGH / MEDIUM / LOW

What I checked            suite, mutation score, vacuity, oracle coverage
What's wrong              1. ...  2. ...
What I could NOT check    ← the part worth reading
```

**The `What I could NOT check` section is mandatory** on anything risky. If the
system can't name what it didn't test, it wasn't thinking, and G7 rejects the
report.

> A report saying "MEDIUM, these three paths are untested, here's why" is a
> success. A green tick with no reasoning is a failure **even when the code is
> fine** — because it teaches everyone to stop reading it.

---

## Honest limits

- **Test generation from code alone is a regression freezer, not a correctness
  check.** The oracle split reduces this; it does not eliminate it. **The
  ceiling is set by your ticket quality** — thin tickets produce a weak oracle,
  and no prompt fixes that.
- **Two runs produce different tests.** The gates make the *result* trustworthy,
  not the process reproducible.
- **It can't test what has no observable outcome.** Those areas need
  instrumentation before they need tests.
- **Every output is a proposal.** A Confidence Report is an input to your
  decision, not a replacement for it.
