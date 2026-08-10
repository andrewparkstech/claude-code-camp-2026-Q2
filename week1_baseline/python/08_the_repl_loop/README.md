# The REPL Loop (Python port)

Python port of `week1_baseline/ruby/08_the_repl_loop`. Same behavior, same
output shape. This step adds `Repl`, an interactive session loop, and a new
top-level entry point, `boukensha.repl()`, that wires up the same primitives
as `boukensha.run()` (`07_the_run_dsl`) but stays alive across multiple
turns instead of returning after one — reading tasks from stdin, running the
agent, and printing replies, sharing one `Context` (and therefore one
accumulating conversation history) across every turn.

## Setup

```bash
cd week1_baseline/python/08_the_repl_loop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## New Files

| File | Description |
|---|---|
| `boukensha/repl.py` | `Repl` — the interactive session loop |
| `boukensha/version.py` | `VERSION = "0.8.0"` — first version constant in the port |

## Updated Files

| File | Change |
|---|---|
| `boukensha/__init__.py` | Added the `repl()` entry point function; added `Repl` and `VERSION` to the re-exports |
| `boukensha/agent.py` | `run()` and `_wrap_up()` now persist the final assistant reply into `context` before returning it, instead of discarding it (see Considerations) |
| `boukensha/client.py` | A 401 response now raises `ApiError("authentication failed (401) — check your API key")` instead of the generic attempt-count message |
| `boukensha/config.py` | `_resolve_dir()` now checks for a `.boukensha` directory in the current working directory before falling back to `~/.boukensha` |
| `boukensha/context.py` | Added `clear_messages()` — wipes conversation history, keeping tools registered |
| `examples/example.py` | Rewritten to call `boukensha.repl(...)` instead of `boukensha.run(...)` |

Everything else (`tool.py`, `message.py`, `errors.py`, `registry.py`,
`prompt_builder.py`, `logger.py`, `run_dsl.py`, `tasks/*.py`,
`backends/*.py`) is an unchanged copy from `07_the_run_dsl` — confirmed by
diffing the Ruby sources, this step doesn't touch them.

*(Ruby's own README for this step has several inaccuracies: it calls this
"Step 7" and references a `07_the_repl_loop` folder and
`examples/step7.rb` — the real folder is `08_the_repl_loop` and the real
file is `examples/example.rb`; its sample banner output omits the
`config:`/`provider:` lines and version number the real banner prints; and
it describes `Logger#turn` as printing a `╔══ turn N ══╗` header to the
screen, but `turn` only writes a JSONL log event — it prints nothing. This
README reflects the actual behavior, confirmed against a live run.)*

## The new primitives

### `Repl`

The interactive session loop. It wraps the same primitives as a single
`boukensha.run()` call, but instead of running once it stays alive: it reads
a task from the user, runs the agent, prints the reply, and loops back to
the prompt. `Context` is shared across every turn so conversation history
accumulates naturally.

Built-in commands (not sent to the agent):

| Command | Effect |
|---|---|
| `/help` | Print the command list |
| `/quiet` | Suppress detailed logging |
| `/loud` | Re-enable logging |
| `/clear` | Wipe conversation history (tools stay registered) |
| `/exit` / `/quit` | Leave the REPL |
| Ctrl-D (EOF) | Leave the REPL silently |
| Ctrl-C | Interrupt — leave the REPL gracefully |

### `boukensha.repl()`

Same signature as `boukensha.run()`, minus `task`. Register tools via
`configure`; then the REPL loop takes over.

```python
def configure(dsl):
    dsl.tool(
        "read_file",
        description="Read a file from disk",
        parameters={"path": {"type": "string", "description": "File path"}},
        block=lambda path: open(path).read(),
    )

boukensha.repl(model="claude-haiku-4-5", configure=configure)
```

| Option | Default | Description |
|---|---|---|
| `system` | the player task's system prompt | System prompt |
| `model` | the player task's configured model | Model name |
| `backend` | the player task's configured provider | `"anthropic"`, `"openai"`, `"gemini"`, `"ollama"`, or `"ollama_cloud"` |
| `api_key` | `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/`GEMINI_API_KEY`/`OLLAMA_API_KEY` (matching `backend`) | API key for the chosen backend; not needed for `"ollama"` |
| `ollama_host` | `"http://localhost:11434"` | Ollama base URL |
| `log` | `None` | Optional path override; by default logs go to `.boukensha/sessions/<session-id>.jsonl` |
| `max_output_tokens` | the player task's configured setting (1024) | Max tokens per API response |
| `configure` | `None` | Optional callable `configure(dsl)` for registering tools |

## Changes from `07_the_run_dsl`

### `Context.clear_messages()`
Wipes `messages` while keeping tools registered. Used by the REPL's
`/clear` command.

### `Agent.run()`/`_wrap_up()` — persist the final reply
Before this step, the agent returned the final text without adding it to
the context. That was fine for one-shot `run()` calls (context is thrown
away anyway), but a REPL needs the full transcript so subsequent turns see
the prior exchange.

```python
# 07_the_run_dsl — final text returned but NOT added to context
return text

# 08_the_repl_loop — final text added to context, then returned
self._context.add_message("assistant", text)
return text
```

### `Config._resolve_dir()` — checks the working directory
Resolution order is now: `BOUKENSHA_DIR` env var, then a `.boukensha`
directory in the current working directory (if one exists), then
`~/.boukensha`.

### `Client.call()` — clearer 401 message
A 401 response now raises `ApiError("authentication failed (401) — check
your API key")` instead of the generic `"API request failed after N
attempts (401): ..."` message.

## What It Looks Like

Running the example and feeding it `/help`, `list the files in the lib
directory`, `what was the first file I asked you about?`, `/exit` produces
output like this (captured from a live run against this repo's
`.boukensha/`, provider `anthropic`, model `claude-haiku-4-5`):

```
Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>

╔══════════════════════════════════════╗
║  BOUKENSHA MUD Assistant (v0.8.0)    ║
╚══════════════════════════════════════╝
  config:    /home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha
  provider:  anthropic (claude-haiku-4-5)  ✓ API key set

  /quiet or /loud   toggle logging
  /clear           reset conversation history
  /exit or /quit    leave the REPL

boukensha> Commands:
  /quiet   suppress logging output
  /loud    re-enable logging output
  /clear   wipe conversation history (tools stay)
  /exit    leave the REPL
  /help    show this message
boukensha> 
...
boukensha> Goodbye.
```

And the corresponding session log — two `"phase":"turn"` events (one per
REPL turn; built-in commands like `/help` don't count), and the second
turn's `"phase":"prompt"` event carries the full accumulated history from
turn one, including the final assistant reply — confirming the
persisted-assistant-reply fix:

```json
{"phase":"session_start","task":"player","max_iterations":25,"max_output_tokens":1024,"model":"claude-haiku-4-5","provider":"anthropic","session_id":"...","at":"..."}
{"phase":"turn","n":1,"session_id":"...","at":"..."}
{"phase":"iteration","n":1,"max":25,"session_id":"...","at":"..."}
...
{"phase":"turn_end","reason":"completed","iterations":1,"tokens":null,"session_id":"...","at":"..."}
{"phase":"turn","n":2,"session_id":"...","at":"..."}
{"phase":"iteration","n":1,"max":25,"session_id":"...","at":"..."}
{"phase":"prompt","message_count":7,"messages":[...,{"role":"assistant","content":"..."},{"role":"user","content":"what was the first file I asked you about?"}],"tool_count":2,"tools":["read_file","list_directory"],"session_id":"...","at":"..."}
...
```

The model's actual tool choice, iteration count, and generated text are
non-deterministic — the banner layout, command echo, blank-line spacing,
and the log's `phase` values/field sets are what should match run to run,
not the exact text.

## Considerations

**`Repl` constructs a new `Agent` every turn, not once.** Carried over
unchanged from Ruby — its own README flags this as a known rough edge it is
deliberately not fixing yet ("we are not fixing these now to preserve
future layers"). `Agent` is nearly stateless (all mutable state it reads —
`context`, `registry`, `logger` — is passed in and shared across turns), so
behavior should be equivalent to reusing one instance, but the construction
itself is repeated every call to `_run_turn`.

**`/quiet` and `/loud` have an unverified effect.** Also carried over
unchanged and unresolved from Ruby's own README: `set_quiet()`/`set_loud()`
toggle a module-level flag (`is_quiet()`) that nothing in this codebase
currently reads. Whether they're meant to gate something not yet wired up,
or are legacy from an earlier design, is an open question — not
investigated this step.

**`LoopError` is now genuinely reachable, though never raised.** `Repl._run_turn`
catches it around `agent.run()`, same as Ruby's `rescue LoopError`. No code
path in this step (or any prior step) actually raises it — same "defined
for parity" status it's had since `05_agent_loop` — but it's the first step
where catching it is live code rather than dead weight.

**Stdin reading uses Python's `input()` builtin.** Ruby's `$stdin.gets`
returns `nil` at EOF; Python's `input(prompt)` raises `EOFError` instead.
`Repl.start()` catches it to break the loop silently — functionally
identical to Ruby's `break unless input`, including the prompt-printing
behavior (`input()` writes its prompt argument to stdout the same way
Ruby's explicit `print PROMPT; $stdout.flush` does).

## Run Example

```bash
./week1_baseline/bin/python/08_the_repl_loop
```

Field-for-field structure (banner layout, command echo, blank-line spacing,
and the session log's `phase` values/field sets) matches the Ruby run
captured in
[docs/plans/python_port/08_the_repl_loop.md](../../../docs/plans/python_port/08_the_repl_loop.md).

## Out of scope

- No MUD connection / no actual `look`/`move` gameplay tools — the example
  still uses the filesystem tools (`read_file`, `list_directory`)
  introduced in `04_api_client`, matching Ruby's own `example.rb`.
- No fix for constructing a fresh `Agent` every REPL turn, and no
  investigation of `/quiet`/`/loud`'s real effect — both carried over
  unchanged per Ruby's own README (see Considerations).
- No task selection — `repl()` hardcodes the `Player` task, matching Ruby
  and matching `07_the_run_dsl`'s `run()`.
- No readline-style history/editing beyond whatever the terminal and
  Python's `input()` provide for free.
- No use of `Logger.subscribe()` by any production code path.
- `Context`/`Registry`'s dual ownership of tools, Ollama's hardcoded
  `http://localhost:11434` default, and `Client` not being fully
  stateless — all carried forward unchanged, same as every prior step.
