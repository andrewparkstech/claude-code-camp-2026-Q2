---
name: port-ruby-to-python
description: Plans and executes a Ruby-to-Python port of one week1_baseline step in this repo (e.g. week1_baseline/ruby/03_prompt_builder -> week1_baseline/python/03_prompt_builder). Use this whenever the user asks to "port" a step, "port the next step", "port ruby to python", or otherwise wants a week1_baseline exercise translated from Ruby into Python. Always writes a plan doc into docs/plans/python_port/ and gets user sign-off before writing any Python code.
---

# Port Ruby to Python

Ports one step of `week1_baseline/ruby/` to `week1_baseline/python/` in this
repo. This is a two-phase workflow — **plan, then (optionally) execute** —
and the two phases must not be collapsed into one. Writing code before the
plan is confirmed defeats the purpose of the skill: the plan is where naming
collisions, scope boundaries, and dependency choices get decided *with* the
user instead of guessed at while writing code.

## Phase 0 — pick the step

List the subfolders under `week1_baseline/ruby/` and ask the user which one
to port. Default to the highest-numbered folder (sorted by the leading
`NN_` prefix, e.g. `04_api_client` beats `03_prompt_builder`) if the user
doesn't specify one. Confirm the corresponding Python port doesn't already
exist at `week1_baseline/python/NN_stepname/` — if it does, ask the user
whether they mean to redo it before proceeding.

## Phase 1 — write the plan

**Do not write any Python code in this phase.** The deliverable is a
markdown plan doc.

1. **Read convention first.** Before drafting anything, read the most
   recent one or two existing plans in `docs/plans/python_port/` (sort by
   the `NN_` prefix, read the highest numbers — they're the most likely to
   reflect the latest conventions and decisions). These existing docs are
   the authoritative style reference, not this skill file — section
   headings, tone, and level of detail should match them, not be reinvented.
   Also skim the corresponding already-ported Python step directories under
   `week1_baseline/python/` to see current patterns in the actual code
   (package layout, error handling, etc.).

2. **Read the Ruby source for the step being ported** —
   `week1_baseline/ruby/NN_stepname/` including its `lib/`, `examples/`,
   and `README.md`. Diff it against the previous Ruby step
   (`diff -r week1_baseline/ruby/<prev> week1_baseline/ruby/<this>`) to see
   exactly what's new versus byte-identical carryover — prior plans lean on
   this diff heavily to decide what can be copied unchanged versus what
   needs fresh translation.

3. **Run the Ruby example** for this step (e.g.
   `./week1_baseline/bin/ruby/NN_stepname`) against the repo's existing
   `.boukensha/` directory and capture the actual output verbatim. This
   becomes the "Verified Ruby output" section — the source of truth the
   Python port must match field-for-field. Don't trust the Ruby README's
   documented output without verifying; prior steps found the README stale
   at least once.

4. **Identify decisions that need the user's input**, and ask before
   writing them into the plan as settled. Typical categories, drawn from
   what prior steps actually hit:
   - Ruby idioms with no direct Python equivalent (symbol/string duality,
     method-name collisions between class-level and instance-level methods,
     `?`/`!`-suffixed method names, block/proc arguments).
   - New third-party dependencies this step's Ruby code pulls in, and
     whether the Python equivalent is a straightforward stdlib or pip swap.
   - Whether known rough edges already carried over from earlier steps
     (check prior plans' "Out of scope" sections) get fixed now or stay
     carried over — default to staying carried over unless the user says
     otherwise, matching precedent.
   - Anything the Ruby README flags as unfinished, stale, or a known issue.

   Don't invent questions for things that already have clear precedent in
   prior plans (e.g. venv-vs-pyproject.toml is already decided — see
   Conventions below) — only ask where this step's Ruby code introduces
   something genuinely new.

5. **Write the plan** to
   `docs/plans/python_port/NN_stepname.md` (matching the Ruby folder's
   `NN_stepname` exactly). Follow the section structure already established
   by the existing docs in that directory:
   - `# Python Port Plan · NN_stepname`
   - Intro paragraph: what's being ported, what it adds on top of the prior
     step, and an explicit statement that this is a straight port of the
     current step only (no scope creep into future steps' concerns).
   - `## Decisions (confirmed with user)` — the outcomes from step 4, each
     with a one-line rationale.
   - `## Target directory layout` — full tree under
     `week1_baseline/python/NN_stepname/`, annotated inline with which files
     are new versus copied unchanged from the prior step.
   - `## Ruby → Python mapping` — a table: Ruby construct, Python
     equivalent, notes. This is the densest and most valuable section in
     prior plans — don't skimp on it.
   - Any config/schema sections relevant to this step, following whatever
     prior steps did (e.g. "Config directory resolution", "Config schema")
     if this step touches config at all.
   - `## Verified Ruby output` — the captured output from step 3, plus a
     one-line note on what it was run against.
   - `## Implementation steps` — numbered, concrete enough that Phase 2 can
     follow them directly without re-deriving decisions.
   - `## Out of scope for this step` — explicit list, including rough edges
     intentionally left broken (cite which prior step introduced them).

6. **Present the plan location to the user** and ask whether to proceed
   with executing it. Do not start Phase 2 without an explicit go-ahead —
   the user may want to edit the plan first.

## Phase 2 — execute (only after user confirms)

Follow the plan's own "Implementation steps" section exactly — that section
is the authoritative task list at this point, not this skill file. General
reminders that apply across all steps:

- Each ported step is a **self-contained directory** —
  `week1_baseline/python/NN_stepname/` gets its own `boukensha/` package,
  `requirements.txt`, etc. Copy unchanged files forward from the previous
  step's Python port rather than importing across step directories, per the
  plan's mapping table.
- Plain `venv` + `requirements.txt` (`PyYAML`, `python-dotenv`, plus
  whatever the plan adds). No `pyproject.toml`, no lockfile, unless the plan
  explicitly says otherwise.
- No test suite — the Ruby steps don't have one either. Verification is
  running the example script and diffing against the "Verified Ruby output"
  section.
- **Always add an entry point script** at
  `week1_baseline/bin/python/NN_stepname` (matching the code folder's name
  exactly), even if the plan's own "Implementation steps" forgot to spell it
  out. Every existing script in `week1_baseline/bin/python/` is byte-identical
  in shape — only the folder name changes — so generate it from that fixed
  template rather than improvising:
  ```bash
  #!/usr/bin/env bash

  cd "$(dirname "$0")/../../python/NN_stepname"
  source .venv/bin/activate
  python examples/example.py
  ```
  Make it executable (`chmod +x`) after writing it.
- Write a `README.md` in the new Python step directory, same shape as the
  Ruby step's `README.md`, adjusted for Python-specific setup and any
  naming divergences the plan's mapping table calls out.
- After implementing, run the new entry point script and confirm the output
  matches the plan's "Verified Ruby output" field-for-field (modulo the
  divergences the plan documents as intentional, e.g. class naming). Report
  any mismatch back to the user rather than silently adjusting the plan's
  intent.
