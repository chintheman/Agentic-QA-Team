---
name: qa-conventions
description: This repository's test conventions — layout, naming, fixtures, factories, authenticated clients, data seeding. Load before writing any test.
---

# Test conventions

> **STATUS: template.** Spec §9 calls this "the highest quality-per-token skill
> in the set — write it carefully and keep it current." It cannot be written
> until the kit is installed in a real repository, because every line of it is a
> fact about that codebase. Replace each `<<PLACEHOLDER>>` on install.
>
> A stale version of this file is worse than none: agents follow it confidently
> and produce tests that reviewers reject wholesale.

## Layout and naming

- Test files live in `<<tests/ | alongside source>>`.
- Naming: `<<*.test.ts | test_*.py>>`.
- **Every test generated from an oracle proposition carries its ID in the name**
  (`O1`, `I2`, `B1`). G1 selects by ID and the marshal counts coverage by it.

## Running

| Task | Command |
|---|---|
| Full suite | `<<TEST_COMMAND>>` |
| Single file | `<<TEST_FILE_COMMAND>>` |
| By name/ID | `<<TEST_ID_COMMAND>>` |
| Coverage | `<<COVERAGE_COMMAND>>` (diagnostic only — never a gate) |

Full-suite wall-clock: `<<N>>` minutes. This number decides whether the mutation
gate is affordable; if it grows, G2's cap starts biting before the score does.

## Fixtures and factories

- Factories: `<<path>>`. Prefer a factory over a literal — a hand-built object
  drifts from the schema and starts passing for the wrong reason.
- Authenticated client: `<<how>>`.
- Seeding: `<<how>>`. Each test owns its data; never depend on another test's
  leftovers. Order-dependence is the flake class that takes longest to diagnose.

## Mocking policy

Mock **only process-edge I/O**: network, clock, filesystem, third-party services.

Never mock the unit under test. A test whose only assertion is
`expect(mock).toHaveBeenCalled()` verifies the test's own wiring and is rejected
by G3.

## Property-based testing

Library: `<<fast-check | Hypothesis | jqwik | proptest>>`.

Prefer one property test over twenty examples when the oracle supplies an
invariant — round-trip, idempotency, order-invariance, conservation,
monotonicity. These hold without ground truth, which is exactly why they survive
refactors that break example-based tests.

## Known traps in this repo

`<<e.g. the clock must be frozen before importing X; the test DB needs a schema
per worker; suite Y is order-dependent>>`
