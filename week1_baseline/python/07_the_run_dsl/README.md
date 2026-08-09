# The `boukensha.run` DSL (Python port)

Python port of `week1_baseline/ruby/07_the_run_dsl`. Same behavior, same
output shape. This step adds a single top-level entry point,
`boukensha.run()`, that hides all the manual plumbing every prior step
required (`Context`, `Registry`, backend selection, `PromptBuilder`,
`Client`, `Logger`, `Agent`) behind one call. It's the "hello world" entry
point described in the plan.

## Setup

```bash
cd week1_baseline/python/07_the_run_dsl
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## New Files

| File | Description |
|---|---|
| `boukensha/run_dsl.py` | `RunDSL` — the tiny object passed to `run()`'s `configure` callback; exposes only `tool()` |

## Updated Files

| File | Change |
|---|---|
| `boukensha/__init__.py` | Added the `run()` entry point function; added `RunDSL` to the re-exports; re-added `LoopError` to the re-exports |
| `boukensha/config.py` | Re-added the `mud_host`/`mud_port`/`mud_username`/`mud_password` properties, previously removed in `06_the_logger` as dead code (see Considerations) |
| `boukensha/errors.py` | Re-added `LoopError`, previously removed in `06_the_logger` (see Considerations) |
| `boukensha/logger.py` | Added `turn(n)` and `subscribe(callback)`; `_write_log` now notifies subscribers after each write |
| `examples/example.py` | Rewritten to call `boukensha.run(...)` instead of manually constructing `Context`/`Registry`/backend/`PromptBuilder`/`Client`/`Logger`/`Agent`; header bumps to Step 7 |

Everything else (`config.py`'s core resolution logic, `tool.py`,
`message.py`, `context.py`, `registry.py`, `client.py`, `prompt_builder.py`,
`agent.py`, `tasks/*.py`, `backends/*.py`) is an unchanged copy from
`06_the_logger` — confirmed by diffing the Ruby sources, this step doesn't
touch them.

*(Ruby's own README for this step has an options table for `Boukensha.run`
that's stale: it lists `token_budget:` and `max_tokens:` params that don't
exist on the real method (it's `max_output_tokens:`, and there's no
context-window kwarg at all), and claims `backend:` defaults to
`:anthropic` and `model:` defaults to `"claude-haiku-4-5"` — the real
defaults are `nil`, falling back to whatever `tasks.player.provider`/
`tasks.player.model` say in `settings.yaml`. The table below reflects the
actual `run_dsl.rb`/`__init__.py` signature.)*

## The new primitive

### `RunDSL`

A tiny host object passed to `run()`'s `configure` callback. It exposes
only `tool()`, keeping the DSL surface intentionally small and preventing
callers from reaching internal state:

```python
def tool(self, name, description, parameters=None, block=None):
    return self._registry.tool(name, description=description, parameters=parameters or {}, block=block)
```

Ruby's `Boukensha.run(&block)` does `RunDSL.new(registry).instance_eval(&block)`,
so `self` inside the block becomes a `RunDSL` and bare `tool "x", ...` calls
resolve against it. Python has no `instance_eval` — the port uses an
explicit `configure=` callback instead, a plain function taking one
positional argument (the `RunDSL` instance):

```python
def configure(dsl):
    dsl.tool(
        "read_file",
        description="Read a file from disk",
        parameters={"path": {"type": "string", "description": "File path"}},
        block=lambda path: open(path).read(),
    )

result = boukensha.run(task="Read lib/boukensha.rb", configure=configure)
```

This mirrors how the per-tool implementation itself is already passed —
`Registry.tool`'s `block=` kwarg, established in `04_api_client` — but uses
a distinct name (`configure`) since it plays a different role: registering
*one or more* tools rather than implementing a single one.

### `boukensha.run()`

Accepts keyword arguments that describe *what* to do. All plumbing is
handled internally.

| Option | Default | Description |
|---|---|---|
| `task` | *(required)* | The user message handed to the agent |
| `system` | the player task's system prompt | System prompt |
| `model` | the player task's configured model | Model name |
| `backend` | the player task's configured provider | `"anthropic"`, `"openai"`, `"gemini"`, `"ollama"`, or `"ollama_cloud"` |
| `api_key` | `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/`GEMINI_API_KEY`/`OLLAMA_API_KEY` (matching `backend`) | API key for the chosen backend; not needed for `"ollama"` |
| `ollama_host` | `"http://localhost:11434"` | Ollama base URL |
| `log` | `None` | Optional path override; by default logs go to `.boukensha/sessions/<session-id>.jsonl` |
| `max_output_tokens` | the player task's configured setting (1024) | Max tokens per API response |
| `configure` | `None` | Optional callable `configure(dsl)` for registering tools |

`run()` always closes its `Logger` before returning or raising
(`try/finally: logger.close()`), unlike `06_the_logger`'s `Logger`, which
was ported but never actually closed by any caller.

## Before and after

**Step 6 — manual plumbing:**

```python
ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)
backend = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model="claude-haiku-4-5")
builder = PromptBuilder(ctx, backend)
client = Client(builder)
logger = Logger()
agent = Agent(ctx, registry, builder, client, logger=logger)

registry.tool("read_file", description="Read a file",
              parameters={"path": {"type": "string"}}, block=lambda path: open(path).read())

ctx.add_message("user", "Read lib/boukensha.rb")
agent.run()
```

**Step 7 — just describe what you want:**

```python
def configure(dsl):
    dsl.tool("read_file", description="Read a file",
              parameters={"path": {"type": "string"}}, block=lambda path: open(path).read())

result = boukensha.run(task="Read lib/boukensha.rb", configure=configure)
```

## What It Looks Like

Running the example produces output like this (captured from a live run
against this repo's `.boukensha/`, provider `anthropic`, model
`claude-haiku-4-5`):

```
=== BOUKENSHA Step 7: The boukensha.run DSL ===

Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>


=== FINAL RESPONSE ===
## Summary of the Boukensha MUD Player Assistant Framework
...
```

And the corresponding session log — `session_start` now carries `task`,
`max_iterations`, `max_output_tokens`, `model`, and `provider` merged in
before `session_id`/`at` (bare in `06_the_logger`, since this is the first
caller to pass a non-empty `snapshot`):

```json
{"phase":"session_start","task":"player","max_iterations":25,"max_output_tokens":1024,"model":"claude-haiku-4-5","provider":"anthropic","session_id":"20260809T223626Z-97486420","at":"2026-08-09T18:36:26-04:00"}
{"phase":"iteration","n":1,"max":25,"session_id":"20260809T223626Z-97486420","at":"2026-08-09T18:36:26-04:00"}
{"phase":"prompt","message_count":1,"messages":[...],"tool_count":2,"tools":["read_file","list_directory"],"session_id":"20260809T223626Z-97486420","at":"2026-08-09T18:36:26-04:00"}
{"phase":"response","text":"(tool use — 1 call)","usage":{...},"stop_reason":"tool_use","task":"player","provider":"anthropic","model":"claude-haiku-4-5","usage_unit":"tokens","input_tokens":703,"output_tokens":56,"cost_usd":0.000983,"session_id":"20260809T223626Z-97486420","at":"2026-08-09T18:36:27-04:00"}
{"phase":"tool_call","name":"read_file","args":{"path":"README.md"},"session_id":"20260809T223626Z-97486420","at":"2026-08-09T18:36:27-04:00"}
{"phase":"tool_result","name":"read_file","result":"...","ok":true,"error":null,"session_id":"20260809T223626Z-97486420","at":"2026-08-09T18:36:27-04:00"}
...
{"phase":"turn_end","reason":"completed","iterations":2,"tokens":null,"session_id":"20260809T223626Z-97486420","at":"2026-08-09T18:36:36-04:00"}
```

The model's actual tool choice, iteration count, and generated text are
non-deterministic — the labeled stdout lines and the log's `phase` values
and field sets are what should match run to run, not the exact text or
iteration count.

## Considerations

**`configure=` vs. Ruby's `instance_eval` block.** Python has no way to
re-target `self` inside a block the way Ruby's `instance_eval` does, so the
DSL surface is a plain callback taking the `RunDSL` instance explicitly
rather than an implicit receiver. Functionally identical — `configure`
still runs exactly once, before the backend is constructed, and its only
capability is calling `dsl.tool(...)`.

**`Logger.turn()` and `Logger.subscribe()` are unused this step.** Both
exist per Ruby's `logger.rb`, ported for parity, but nothing in `run_dsl`,
`agent.py`, or `example.py` calls either — no code path in this step drives
per-turn logging separately from `iteration`, and nothing subscribes to the
event stream. Same "defined for a later step, dead in this one" treatment
`06_the_logger` gave `Logger.close()`.

**`mud_host`/`mud_port`/`mud_username`/`mud_password` and `LoopError` are
back, still unused.** `06_the_logger`'s port removed them as dead code, but
Ruby's step 7 source re-adds them verbatim — this port mirrors that
re-addition for literal parity rather than re-litigating the "unused code"
call, even though nothing calls any of the four properties or raises
`LoopError` in this step either.

**`Logger.close()` is now actually called.** Reversing `06_the_logger`'s
behavior: `run()` wraps its body in `try/finally: logger.close()`, so the
session file's handle is released deterministically on every path out of
`run()`, success or exception.

**Backend selection uses plain strings, not an enum/symbol type.** Ruby's
`backend:` param is a `Symbol` (`:anthropic`, `:ollama`, ...) matched with
`case`. Python has no symbol/string duality to preserve, so `backend` is
just a string compared with `==` down an if/elif chain — `"anthropic"`,
`"openai"`, `"gemini"`, `"ollama"`, `"ollama_cloud"`.

## Run Example

```bash
./week1_baseline/bin/python/07_the_run_dsl
```

Field-for-field structure (labeled header lines, blank-line spacing,
`=== FINAL RESPONSE ===`, and the session log's `phase` values/field sets)
matches the Ruby run captured in
[docs/plans/python_port/07_the_run_dsl.md](../../../docs/plans/python_port/07_the_run_dsl.md).

## Out of scope

- No MUD connection / no actual `look`/`move` gameplay tools — the example
  still uses the filesystem tools (`read_file`, `list_directory`)
  introduced in `04_api_client`, matching Ruby's own `example.rb`. The
  re-added `mud_*` Config properties stay unused.
- No task selection — `run()` hardcodes the `Player` task, matching Ruby;
  no mechanism to choose a different task class exists yet.
- No use of `Logger.turn`/`Logger.subscribe` by any production code path.
- `Context`/`Registry`'s dual ownership of tools, flagged in the
  `02_the_registry` port's README, is still unresolved here — carried
  forward unchanged.
- Ollama's backend still hardcodes `http://localhost:11434` as its default
  rather than reading an env var, and `Client` still holds `builder` as
  instance state rather than being fully stateless — both carried forward
  unchanged to match Ruby.
