#!/usr/bin/env bash
# Adapter: Python with pytest + mutmut.
QA_ADAPTER_NAME="python-pytest"

# Resolve a working pytest rather than assuming `python3 -m pytest`. A pytest
# installed by uv/pipx lives in its own venv and is importable only by that
# venv's interpreter, so the module form fails while the console script works.
# Getting this wrong makes every test run look like a collection error, which
# G1 then reports as INCONCLUSIVE — a gate silently measuring nothing.
qa_pytest() {
  if [[ -z "${QA_PYTEST_CMD:-}" ]]; then
    if python3 -c "import pytest" >/dev/null 2>&1; then
      QA_PYTEST_CMD="python3 -m pytest"
    elif command -v pytest >/dev/null 2>&1; then
      QA_PYTEST_CMD="pytest"
    else
      echo "no pytest available (tried 'python3 -m pytest' and 'pytest')" >&2
      return 90
    fi
  fi
  # rootdir on sys.path so `from src... import` works without an installed package.
  $QA_PYTEST_CMD -p no:cacheprovider --rootdir . "$@"
}

qa_test_all()   { PYTHONPATH="${PYTHONPATH:-}:$PWD" qa_pytest -q; }
qa_test_files() { PYTHONPATH="${PYTHONPATH:-}:$PWD" qa_pytest -q "$@"; }

# Verbose on purpose: G1 must be able to find the specific test ID in the
# output to distinguish a named assertion failure from generic noise.
qa_test_ids()   {
  local pat; pat="$(printf '%s or ' "$@")"
  PYTHONPATH="${PYTHONPATH:-}:$PWD" qa_pytest -v -k "${pat% or }"
}

# Mutation testing with mutmut 3.
#
# mutmut 3's `run` subcommand takes only --max-children; there is no
# --paths-to-mutate flag (that was mutmut 2). Source selection comes from
# configuration, so the scope is written into setup.cfg for the duration of the
# run and restored afterwards.
#
# Two caveats worth knowing before you trust a number from this:
#
#   * mutmut 3 copies the source into a mutants/ directory and runs the suite
#     from there. A repository whose conftest.py manipulates sys.path relative
#     to its own location can fail to import under mutation while passing
#     normally. PYTHONPATH is exported to compensate; if collection still fails,
#     that is a real integration problem and the gate should report
#     MISCONFIGURED rather than a score.
#   * mutmut has no per-file selection, so scoping is by DIRECTORY. When the
#     changed files span directories the run is wider than the diff, which costs
#     wall-clock and makes the G2 cap matter more.
qa_mutation() {
  command -v mutmut >/dev/null 2>&1 || {
    echo "mutmut is not installed — the mutation gate cannot run. This is a" >&2
    echo "misconfiguration, not a passing gate: install it or report G2 as" >&2
    echo "unavailable in every Confidence Report." >&2
    return 90
  }

  local files=("$@")
  local dirs=() f d
  for f in "${files[@]}"; do
    d="$(dirname "$f")"
    [[ "$d" == "." ]] && d="$f"          # top-level module: mutate the file itself
    [[ " ${dirs[*]} " == *" $d "* ]] || dirs+=("$d")
  done
  [[ ${#dirs[@]} -gt 0 ]] || { echo "no mutation scope resolved" >&2; return 91; }

  local backup="" had_cfg=0
  if [[ -f setup.cfg ]]; then
    had_cfg=1; backup="$(mktemp)"; cp setup.cfg "$backup"
  fi
  restore_cfg() {
    if [[ "$had_cfg" -eq 1 ]]; then cp "$backup" setup.cfg; rm -f "$backup"
    else rm -f setup.cfg; fi
  }
  trap restore_cfg RETURN

  # `source_paths`; `paths_to_mutate` is accepted but deprecation-warns.
  {
    echo ""
    echo "[mutmut]"
    echo "source_paths=$(IFS=,; echo "${dirs[*]}")"
  } >> setup.cfg

  PYTHONPATH="${PYTHONPATH:-}:$PWD" mutmut run --max-children 4 >&2 || true
  mutmut export-cicd-stats >/dev/null 2>&1 || true

  mutmut results --all true 2>/dev/null \
    | python3 "$QA_ROOT/.qa/gates/mutmut_normalise.py" > "$QA_MUTATION_JSON"
  local rc=${PIPESTATUS[1]}
  [[ $rc -eq 0 ]] || { echo "mutmut output could not be normalised (rc=$rc)" >&2; return "$rc"; }
}

qa_vacuity() { python3 "$QA_ROOT/.qa/gates/py_vacuity.py" "$@"; }

qa_coverage() {
  PYTHONPATH="${PYTHONPATH:-}:$PWD" qa_pytest -q --cov --cov-report=json >/dev/null 2>&1 || true
  python3 -c "import json;print(json.load(open('coverage.json'))['totals']['percent_covered']/100)" 2>/dev/null || echo 0
}

qa_route_inventory() {
  if [[ -f openapi.json ]]; then
    jq -r '.paths | to_entries[] | .key as $p | .value | keys[] | (ascii_upcase + " " + $p)' openapi.json
  else
    echo "no openapi.json; implement qa_route_inventory for this repo" >&2; return 92
  fi
}

qa_bootstrap_worktree() {
  local wt="$1"
  [[ -n "${VIRTUAL_ENV:-}" ]] && ln -sfn "$VIRTUAL_ENV" "$wt/.venv"
  [[ -f .env.test ]] && cp .env.test "$wt/.env.test"
  echo "QA_DB_SCHEMA=qa_$(basename "$wt")" >> "$wt/.env.test"
  ( cd "$wt" && qa_test_all >/dev/null 2>&1 ) || {
    echo "bootstrap verification failed: suite is not green in $wt" >&2; return 93; }
}
