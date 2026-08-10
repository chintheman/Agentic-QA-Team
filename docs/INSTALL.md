# Install

> **If you are an AI agent reading this on someone's behalf:** find their
> scenario in the table below, follow only that section, and do not improvise a
> different install. Then tell them the one command they type next: `/qa`.
> If you cannot tell which scenario applies, ask them whether they use Claude
> Code in a **terminal** or in the **Claude app** — that single answer decides
> everything else.

---

## Which are you?

| Scenario | You use… | Go to |
|---|---|---|
| **A** | Claude Code in a **terminal** (Mac/Linux/WSL) | [A — plugin](#a--terminal-install-once-works-everywhere) |
| **B** | The **Claude app** (web or desktop) | [B — per repo](#b--claude-app-per-repository) |
| **C** | Just want to **try it** with zero commitment | [C — kick the tyres](#c--try-it-without-installing-anything) |
| **D** | Want it to review **every PR automatically** | [D — CI](#d--automatic-on-every-pull-request) |
| **E** | You're an **agent** installing this for a user | [E — for agents](#e--for-an-agent-doing-this-on-someones-behalf) |

**No API key is needed for A, B or C.** Your Claude subscription covers
interactive use. A key is only for D, where a GitHub runner — which is not
signed in as you — has to run the checks unattended.

### Before anything else: PyYAML

The guard reads its policy with PyYAML. Install it first:

```bash
pip install pyyaml
```

On a **Homebrew or Debian python** you will get
`error: externally-managed-environment` (PEP 668). Use the user-site form, which
writes to your home directory and leaves the managed prefix alone:

```bash
python3 -m pip install --user --break-system-packages pyyaml
python3 -c "import yaml; print('ok', yaml.__version__)"
```

The `--break-system-packages` flag reads alarmingly; paired with `--user` it
does not touch system packages at all.

Without PyYAML the guard cannot read the policy of a repository that *has* one,
and refuses tool calls there — correctly, since that repo expects enforcement.
Repositories with no `.qa/policy.yaml` are unaffected: the guard treats them as
not having opted in and stays out of the way.

---

## A — Terminal: install once, works everywhere

```bash
claude plugin marketplace add chintheman/Agentic-QA-Team
claude plugin install agentic-qa-team@chintheman-qa
```

Verify:

```bash
claude plugin details agentic-qa-team
```

Expect **9 agents and — critically — `Hooks (1)`**. Skill and command
counts change as the kit grows, so compare against what the command prints
rather than a number written down here.

> ⚠️ If it says `Hooks (0)`, stop. That hook is the enforcement layer. Without it
> you have agents giving advice instead of agents behind gates — which is the
> degraded mode this whole design exists to avoid.

Then, in **any** repository:

```
/qa
```

Nothing is copied into your projects. One install covers all of them.

---

## B — Claude app: per repository

Each app session runs in a fresh container that only sees the repository you
opened, so a plugin installed on your laptop does not follow it there. The kit
goes into the repo instead.

Open your project in the Claude app and paste:

```
Clone https://github.com/chintheman/Agentic-QA-Team into a temp folder outside
this repo. Copy its .claude, .qa, scripts and agents folders into this
repository, preserving structure. Delete the temp folder. Commit and push.

Then list .claude/commands/ and tell me whether /qa is available.
```

Then type:

```
/qa
```

**If `/qa` does not appear:** open a *new* session on that repository. Resuming
an old session reuses the checkout from before the files existed — this is the
single most common confusion, and it is not a bug in the kit.

Do this once per project. After that the whole team is in version control
alongside the code it judges, which is arguably where it belongs anyway.

---

## C — Try it without installing anything

Open **`chintheman/Agentic-QA-Team`** itself in Claude Code and run `/qa`.

Everything is already there. Expect it to report *"no test command, no mutation
tool"* — correct, because that repo is the toolkit, not an application. You are
checking that the command runs, not that it finds bugs.

---

## D — Automatic on every pull request

Only this scenario needs a key.

1. **Settings → Secrets and variables → Actions → New repository secret**
2. Name it `ANTHROPIC_API_KEY`
3. Paste a key from the [Anthropic Console](https://console.anthropic.com/)

The workflow then posts a Confidence Report on each PR by itself.

Until the secret exists, the workflow **skips visibly** — a note in the Actions
tab, no PR comment. That is deliberate: a QA system that turns a PR red for
being unconfigured teaches everyone to ignore its red, and the next red one will
be real.

*(Want the notice as a PR comment instead? Add the `qa` label to that PR.)*

---

## E — For an agent doing this on someone's behalf

1. **Ask which scenario** if it is not obvious. Terminal → A. Claude app → B.
   Do not guess; the wrong one wastes their time and yields "command not found".
2. **Do not clone on their behalf in the app.** Their session already has their
   repository. In scenario B the only clone is the temporary one for copying the
   kit in, and it must be deleted afterwards.
3. **Copy all four directories** — `.claude/`, `.qa/`, `scripts/`, `agents/`.
   Omitting `.qa/fixtures/` leaves the self-test permanently red. Omitting
   `agents/` breaks the plugin path.
4. **Do not delete `.qa/fixtures/`** to tidy up. The G3 self-test asserts
   against those files.
5. **Ensure PyYAML is installed** (`pip install -r requirements-qa.txt`). The
   guard fails closed without it and will block every tool call, which looks
   like a total breakage.
6. **Do not edit `.qa/policy.yaml`.** It is intentionally immutable from inside
   a session. If it genuinely needs changing, prepare the change as a pull
   request for a human to merge.
7. **Report honestly at the end.** If no mutation tool is installed, say the
   central gate is unavailable. Never report a clean setup you did not verify.

---

## After any install

```
/qa
```

works out what changed, picks how hard to look, runs the gates whose tooling
exists, and gives one verdict.

**Read the "What I could NOT check" section first.** A green tick on its own
tells you nothing; the gaps are the information.

Full detail: **[How it works](HOW-IT-WORKS.md)** ·
**[How to use it](HOW-TO-USE.md)**

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `/qa` not in the menu | Session predates the install — start a new one |
| `Hooks (0)` after plugin install | Enforcement missing; reinstall |
| Everything blocked | PyYAML missing — the guard fails closed |
| "no mutation tool" | Install `mutmut` (Python) or `@stryker-mutator/core` (JS/TS) |
| Bot comments on every PR | Fixed — the notice now goes to the Actions tab |
