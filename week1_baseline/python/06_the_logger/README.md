# The Logger (Python port)

Python port of `week1_baseline/ruby/06_the_logger`. Same behavior, same
output shape (aside from the display divergences noted below). This step
adds `Logger`, a structured JSONL file logger, and wires it into every phase
of `Agent`'s loop. It's a file logger, not user-facing display output — the
`[iteration N/max]` and `tool call/result →` lines `05_agent_loop` printed
to stdout are gone; that information now lives in the session log instead.

## Setup

```bash
cd week1_baseline/python/06_the_logger
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## New Files

| File | Description |
|---|---|
| `boukensha/logger.py` | Structured JSONL session logger, one method per event phase |

## Updated Files

| File | Change |
|---|---|
| `boukensha/agent.py` | `__init__` gained a `logger=` param (defaults to a fresh `Logger()`); `run`, `_wrap_up`, and `_handle_tool_calls` now call into the logger at every phase; the `[iteration N/max]` and `tool call/result →` `print()` calls are removed |
| `boukensha/config.py` | Removed the never-used `mud_host`/`mud_port`/`mud_username`/`mud_password` properties (dead code — no MUD connection exists in either language yet) |
| `boukensha/errors.py` | Removed `LoopError` (it was already dead code as of `05_agent_loop` — never raised anywhere) |
| `boukensha/__init__.py` | Added `set_quiet()`/`set_loud()`/`is_quiet()`, `set_debug()`/`is_debug()`, `get_config()` module-level functions; added `Logger` to the re-exports; dropped `LoopError` |
| `examples/example.py` | Constructs a `Logger()` and passes it into `Agent(...)`; header text bumps to Step 6 |

Everything else (`config.py`'s core resolution logic, `tool.py`,
`message.py`, `context.py`, `registry.py`, `client.py`, `prompt_builder.py`,
`tasks/*.py`, `backends/*.py`) is an unchanged copy from `05_agent_loop` —
confirmed by diffing the Ruby sources, this step doesn't touch them.

*(Ruby's own README for this step lists a "Logger API" table that's stale
in multiple ways: `iteration(n:)` is missing its `max:` param,
`prompt(messages:, tools:, budget:)` claims a `budget:` param that doesn't
exist, `tool_result(name:, result:)` is missing `ok:`/`error:`,
`response(text:, usage:, task:, backend:)` is missing `stop_reason:`, and
`limit_reached`, `turn_end`, and `close` are omitted entirely. The table
below reflects the actual `logger.rb`/`logger.py` methods. The Ruby
README's "Run Example" command is also missing a path segment
— `./week1_baseline/bin/06_the_logger` should be
`./week1_baseline/bin/ruby/06_the_logger` — though that doesn't affect this
Python port's own run command below.)*

## Session Logs

Each `Logger` instance generates a session id and writes one log file for
that session:

```text
.boukensha/sessions/<session-id>.jsonl
```

Every line is a complete JSON object with `session_id` and `at` fields
(appended last) plus phase-specific data, keyed by `phase`. This keeps logs
grep/tail friendly and machine readable.

## Logger API

| Method | Phase | Logs |
|---|---|---|
| `iteration(n, max)` | `iteration` | loop counter and ceiling |
| `limit_reached(kind, n, max)` | `limit_reached` | fired when the iteration ceiling is hit, right before wind-down |
| `prompt(messages, tools)` | `prompt` | message count + serialized messages, tool count + tool names |
| `tool_call(name, args)` | `tool_call` | tool name and arguments |
| `tool_result(name, result, ok=True, error=None)` | `tool_result` | tool result (stringified), success flag, error message on failure |
| `response(text, usage=None, stop_reason=None, task=None, backend=None)` | `response` | response text, normalized token usage, stop reason, task/provider/model, estimated cost |
| `raw(data)` | `raw` | full raw provider response — only written when `boukensha.is_debug()` is true |
| `turn_end(reason, iterations, tokens=None)` | `turn_end` | why the turn ended (`"completed"` or a wind-down reason) and how many iterations it took |
| `close()` | — | closes the underlying file handle; defined for parity with Ruby but never called during a normal run (see Considerations) |

Model response lines include the active task, provider, model, normalized
token counts, and estimated USD cost when the backend has token pricing
data:

```json
{"phase":"response","text":"...","usage":{...},"stop_reason":"end_turn","task":"player","provider":"anthropic","model":"claude-haiku-4-5","usage_unit":"tokens","input_tokens":4732,"output_tokens":428,"cost_usd":0.006872,"session_id":"...","at":"..."}
```

## Task Configuration

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
```

When `prompt_override.system` is true, Boukensha reads
`.boukensha/prompts/player/system.md`. Otherwise it falls back to this
step's shipped `prompts/system.md`. This step adds no new settings keys.

Default usage:

```python
logger = Logger()
agent = Agent(ctx, registry, builder, client, logger=logger)
```

You can also provide a session id or override the destination directory:

```python
Logger(session_id="manual-session")
Logger(dir="/tmp/boukensha-sessions")
```

`log=` still accepts an explicit file path for full control, but normal
usage should write under `.boukensha/sessions`.

## Debug Events

Call `boukensha.set_debug()` before running the agent to include raw
provider responses in the log:

```python
import boukensha
boukensha.set_debug()
```

## What It Looks Like

Running the example produces output like this (captured from a live run
against this repo's `.boukensha/`, provider `anthropic`, model
`claude-haiku-4-5`):

```
=== BOUKENSHA Step 6: The Logger ===

Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Max iterations: 25
Max output tokens: 1024


=== FINAL RESPONSE ===
Based on my exploration of the codebase, here's a summary of what the **Boukensha MUD Player Assistant Framework** can do:
...
```

Note there are no `[iteration N/max]` or `tool call/result →` lines in
stdout — that visibility moved entirely into the session log, e.g.:

```json
{"phase":"session_start","session_id":"20260809T220841Z-8a40feb1","at":"2026-08-09T18:08:41-04:00"}
{"phase":"iteration","n":1,"max":25,"session_id":"20260809T220841Z-8a40feb1","at":"2026-08-09T18:08:41-04:00"}
{"phase":"prompt","message_count":1,"messages":[...],"tool_count":2,"tools":["read_file","list_directory"],"session_id":"20260809T220841Z-8a40feb1","at":"2026-08-09T18:08:41-04:00"}
{"phase":"response","text":"(tool use — 1 call)","usage":{...},"stop_reason":"tool_use","task":"player","provider":"anthropic","model":"claude-haiku-4-5","usage_unit":"tokens","input_tokens":703,"output_tokens":56,"cost_usd":0.000983,"session_id":"20260809T220841Z-8a40feb1","at":"2026-08-09T18:08:42-04:00"}
{"phase":"tool_call","name":"read_file","args":{"path":"README.md"},"session_id":"20260809T220841Z-8a40feb1","at":"2026-08-09T18:08:42-04:00"}
{"phase":"tool_result","name":"read_file","result":"# The Logger (Python port)\n...","ok":true,"error":null,"session_id":"20260809T220841Z-8a40feb1","at":"2026-08-09T18:08:42-04:00"}
...
{"phase":"turn_end","reason":"completed","iterations":6,"tokens":null,"session_id":"20260809T220841Z-8a40feb1","at":"2026-08-09T18:08:53-04:00"}
```

The model's actual tool choice, iteration count, and generated text are
non-deterministic — the labeled stdout lines and the log's `phase` values
and field sets are what should match run to run, not the exact text or
iteration count.

## Considerations

**`Logger` is a plain file writer, not `logging`-backed.** It opens its own
file handle and writes newline-delimited JSON directly — no formatter,
handler, or logger hierarchy from Python's stdlib `logging` module,
matching Ruby's own bespoke `File.open`/`puts` implementation.

**The assistant's reasoning gets logged even when it's just a tool-use
preamble.** When a response is pure tool calls with no text, `_handle_tool_calls`
logs a synthesized placeholder like `"(tool use — 2 calls)"` instead of an
empty string, so every `response` event always has non-empty `text`.

**A failing tool doesn't crash the turn.** `_handle_tool_calls` wraps each
tool dispatch in `try/except Exception`. A failure gets logged as
`tool_result(..., ok=False, error=...)` and the stringified error is fed
back to the model as the tool result, so the agent can react to it instead
of the whole run aborting.

**Two independent `Config` instances can exist per run.** `examples/example.py`
constructs its own `Config()` for prompt resolution, while `Logger`'s default
directory comes from `boukensha.get_config()`, a separate lazily-memoized
module-level singleton. Both resolve to the same directory deterministically,
so this is harmless — it mirrors Ruby's own `Boukensha.config` / `Config.new`
split exactly.

**Setter/getter naming for module state.** Ruby's `Boukensha.quiet!`/`.quiet?`
and `.debug!`/`.debug?` are bang-setter/question-getter pairs on the same
word — stripping punctuation the way prior steps dropped `!`/`?` (e.g.
`validate_model!` → `validate_model`) would collide here, since both would
become `quiet()`. This port uses explicit `set_quiet()`/`is_quiet()` and
`set_debug()`/`is_debug()` instead. `set_quiet`/`set_loud`/`is_quiet` are
defined for parity but never actually checked anywhere, matching Ruby.

**`mud_host`/`mud_port`/`mud_username`/`mud_password` and `LoopError` are
gone, not carried forward.** Both were already dead code (no MUD connection
exists yet; nothing ever raised `LoopError`) and Ruby's own diff for this
step deletes them outright — this port mirrors that deletion rather than
keeping unused code around.

**`Logger.close()` is never called.** It exists for parity with Ruby, which
also never calls it in `agent.rb` or `example.rb` — the file handle stays
open for the process's lifetime during a normal run.

## Run Example

```bash
./week1_baseline/bin/python/06_the_logger
```

Field-for-field structure (labeled header lines, blank-line spacing,
`=== FINAL RESPONSE ===`, and the session log's `phase` values/field sets)
matches the Ruby run captured in
[docs/plans/python_port/06_the_logger.md](../../../docs/plans/python_port/06_the_logger.md).

## Ruby → Python idiom differences

- **Camel-to-snake-case backend naming.** `Logger._provider_name` derives
  the logged `provider` field from `type(backend).__name__` (e.g.
  `"OllamaCloud"`) via the same regex-based conversion Ruby uses on
  `backend.class.name.split("::").last` — Python classes aren't
  namespaced with `::`, so there's no `split` step needed, but the
  camelCase → `snake_case` regex itself is identical.
- **Mutable default argument avoided.** Ruby's `Logger#initialize(...,
  snapshot: {})` safely gets a fresh `{}` per call. Python's
  `def __init__(self, ..., snapshot=None)` avoids the classic
  shared-mutable-default pitfall by defaulting to `None` and substituting
  `{}` inside the method body.
- **`Agent.__init__`'s `logger=Logger()` default.** Ruby's
  `logger: Logger.new` constructs a brand-new `Logger` per `Agent.new` call
  with no explicit logger. Python can't use a call as a default argument
  value safely (it would only evaluate once, at function-definition time,
  and be shared across every `Agent()` call that doesn't pass one) — so the
  port uses `logger=None` and constructs `Logger()` inside `__init__` when
  none was given, reproducing "always get *some*, fresh, logger" behavior
  without the shared-default pitfall.
- `ISO 8601` timestamps: Ruby's `Time.now.iso8601` becomes
  `datetime.now().astimezone().isoformat(timespec="seconds")` — both
  produce a local-offset timestamp at second precision (e.g.
  `2026-08-09T18:08:41-04:00`).

## Out of scope

- No MUD connection / no actual `look`/`move` gameplay tools — the example
  still uses the filesystem tools (`read_file`, `list_directory`)
  introduced in `04_api_client`, matching Ruby's own `example.rb`.
- No log rotation, retention, or reading/querying of past session files —
  `Logger` only ever appends to its own session's file.
- No new config keys — `Logger`'s `dir`/`session_id`/`log` overrides are
  constructor kwargs only, never read from `settings.yaml`.
- `Context`/`Registry`'s dual ownership of tools, flagged in the
  `02_the_registry` port's README, is still unresolved here — carried
  forward unchanged.
- Ollama's backend still hardcodes `http://localhost:11434` rather than
  reading an env var, and `Client` still holds `builder` as instance state
  rather than being fully stateless — both acknowledged as known trade-offs
  in Ruby's own README, carried forward unchanged to match.
</content>
