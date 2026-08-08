# Why the agents exist in two directories

`.claude/agents/` is canonical. The top-level `agents/` holds identical copies.

Two install paths need the same nine agents, and the loader is not flexible:

| Install path | Reads agents from |
|---|---|
| Copy `.claude/` into a repo | `.claude/agents/` |
| `claude plugin install` | **top-level `agents/` only** |

A plugin manifest with an explicit `agents: [...]` list pointing into
`.claude/agents/` **passes validation and then silently loads nothing** —
confirmed by installing the plugin and reading `claude plugin details`, which
showed `Agents (0)`. Only auto-discovery from a top-level `agents/` directory
works. That silent-success-then-no-effect behaviour is worth remembering: the
validator is not evidence that a component loaded.

## Rules for `agents/`

- **Agent definitions only.** Every `.md` file there is loaded as an agent, with
  no exemptions — a `README.md` in that directory becomes an agent called
  "README". Documentation belongs here in `docs/` instead.
- **Never edit it directly.** Edit `.claude/agents/`, then run
  `scripts/qa-sync-agents.sh`.

## Drift is gated, not promised

Duplication rots. `.qa/selftest/run.sh` runs `qa-sync-agents.sh --check` and
fails if the two directories disagree, so the copies cannot quietly diverge.
