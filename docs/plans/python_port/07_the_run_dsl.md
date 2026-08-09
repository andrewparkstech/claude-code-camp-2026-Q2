# Python Port Plan · 07_the_run_dsl

Port `week1_baseline/ruby/07_the_run_dsl` to `week1_baseline/python/07_the_run_dsl`,
preserving behavior and output shape exactly. This step adds a single
top-level entry point, `Boukensha.run`, that hides all the manual plumbing
every prior step required (`Context`, `Registry`, backend selection,
`PromptBuilder`, `Client`, `Logger`, `Agent`) behind one call: you describe
*what* to do (a task, optionally a system prompt/model/backend/API key/log
path/output-token cap) and register tools via a small DSL host object
(`RunDSL`, exposing only `tool`), and `Boukensha.run` wires everything
together, runs the agent, and closes the logger. It's a straight port of the
current step only: no MUD connection wiring, no changes to `Agent`'s
control-flow logic (it's byte-identical to `06_the_logger`) — no scope creep
into future steps' concerns.

Confirmed via `diff -rq` against `06_the_logger`: the only Ruby-side changes
are a new `lib/boukensha/run_dsl.rb` (the `RunDSL` class), `boukensha.rb`
(gains the module-level `self.run` method plus `require_relative
"boukensha/tasks/player"` up top and a `require_relative
"boukensha/run_dsl"` at the bottom), `logger.rb` (adds `turn(n:)` and
`subscribe(&block)`, both unused by anything in this step — see mapping
table), `errors.rb` (**re-adds** `LoopError`, previously removed in
`06_the_logger`), `config.rb` (**re-adds** the four `mud_*` dig-helpers,
also previously removed in `06_the_logger`), and a rewritten
`examples/example.rb`. `agent.rb`, `context.rb` (only whitespace
realignment), `client.rb`, `tool.rb`, `message.rb`, `registry.rb`,
`tasks/base.rb`, `tasks/player.rb`, all `backends/*.rb` are byte-identical
(or functionally unchanged) — copy the Python versions forward unchanged.

## Decisions (confirmed with user)

- **The outer DSL block → a `configure=` callback.** Ruby's `Boukensha.run(&block)`
  does `RunDSL.new(registry).instance_eval(&block) if block`, so `self`
  inside the block becomes the `RunDSL` and bare `tool "x", ... do |args| ... end`
  calls resolve against it. Python has no `instance_eval`. The existing
  Python port already resolved the *inner* per-tool block as a plain
  callable passed via `Registry.tool`'s `block=` kwarg (see
  `05_agent_loop`/`06_the_logger`). The *outer* block gets its own distinct
  name rather than overloading `block=` for a different shape: `boukensha.run(task=...,
  ..., configure=None)`, where `configure` is an optional plain function
  taking one positional argument (the `RunDSL` instance) and calling
  `dsl.tool(...)` on it zero or more times before `run()` continues. `RunDSL.tool`
  itself forwards straight to `Registry.tool` (name, description, parameters,
  block=), matching the inner-block precedent exactly. Called once, before
  backend construction, mirroring where Ruby's `instance_eval` runs.
- **`LoopError` and the four `mud_*` Config properties: re-added for literal
  parity with Ruby.** Both were deliberately removed from the Python port in
  `06_the_logger` as dead code (nothing called them in either language).
  Ruby's step 7 source re-adds them verbatim, still unused. The Python port
  mirrors the re-addition exactly — `class LoopError(Exception): pass` back
  in `errors.py` (and back in `__init__.py`'s re-exports), and
  `mud_host`/`mud_port`/`mud_username`/`mud_password` back as `@property`
  methods on `Config` — even though nothing in `run_dsl.py`, `agent.py`, or
  `example.py` references any of them this step either. Same treatment as
  `Logger.close` in `06_the_logger`: ported because Ruby has it, not because
  it's exercised.
- **`Logger.turn(n:)` and `Logger.subscribe(&block)`: ported, both unused
  this step.** Ruby adds both to `logger.rb` but neither `run_dsl.rb` nor
  `agent.rb` nor `example.rb` calls either one — no code path in this step
  drives an iteration through `turn` (that's still `Agent`'s `iteration`
  event) or registers a subscriber. Ported for parity regardless, same
  "defined for a future step, dead in this one" treatment as `Logger.close`
  and `LoopError`. `subscribe` takes a plain callable (Python has no
  `&block`), stored in a list, invoked with each event dict inside
  `_write_log` after the file write.
- **`Logger.close()` is now actually called.** Reversing `06_the_logger`'s
  "ported but never invoked" note: `Boukensha.run` wraps its body in
  `ensure logger&.close`. The Python `run()` does the same with
  `try/finally: logger.close()`, opened right after `Logger(...)` is
  constructed, closed unconditionally on the way out (success or
  exception).
- **`Logger.__init__`'s `snapshot:` is now exercised.** `run_dsl.rb` passes
  `snapshot: {task:, max_iterations:, max_output_tokens:, model:, provider:}`
  into `Logger.new`, so `session_start` now carries those five fields merged
  in (confirmed live in the Verified Ruby output below) — `06_the_logger`'s
  `snapshot={}` param existed but every caller left it empty. No code change
  needed in `logger.py` itself (the parameter was already there); this is
  just `run()`'s call site putting it to use.
- **Backend selection cascade → Python if/elif on plain strings, no
  `Symbol`.** Ruby's `backend ||= task_class.provider(task_settings).to_sym`
  plus a `case backend when :anthropic ... end` becomes
  `backend = backend or task_class.provider(task_settings)` (a plain
  string) plus an if/elif chain comparing against `"anthropic"`,
  `"openai"`, `"gemini"`, `"ollama"`, `"ollama_cloud"` — Python has no
  symbol/string duality to preserve. Same treatment prior steps gave
  Ruby symbol keys.
- **Stale README table, same precedent as `02_the_registry`/`04_api_client`/
  `05_agent_loop`/`06_the_logger`.** Ruby's `07_the_run_dsl/README.md`
  options table for `Boukensha.run` lists `token_budget:` and `max_tokens:`
  params that don't exist on the real method (it's `max_output_tokens:`,
  and there is no context-window/token-budget kwarg at all), claims
  `backend:` defaults to `:anthropic` (the real default is `nil`, falling
  back to `tasks.player.provider` from `settings.yaml`), and claims `model:`
  defaults to `"claude-haiku-4-5"` (the real default is `nil`, falling back
  to `tasks.player.model`). This plan documents the actual `run_dsl.rb`
  keyword list (below); the Python README does the same instead of copying
  Ruby's table. (Unlike `06_the_logger`, this README's "Run Example" command
  — `./bin/ruby/07_the_run_dsl` — and section structure are otherwise
  accurate; only the options table is stale.)
- Everything else follows the precedent already set by `00_config` through
  `06_the_logger`: self-contained per-step directory (duplicate `boukensha/`
  package rather than import across step directories), plain `venv` +
  `requirements.txt` (no new dependency), no test suite, entry point script
  at `week1_baseline/bin/python/07_the_run_dsl`.

## Target directory layout

```
week1_baseline/python/07_the_run_dsl/
  requirements.txt          # PyYAML, python-dotenv (unchanged)
  README.md                 # same section shape as Ruby's, options table corrected (see Decisions)
  prompts/
    system.md                # unchanged content, copied forward from 06_the_logger
  boukensha/
    __init__.py              # adds run() and RunDSL export; LoopError re-added to re-exports
    config.py                # updated — mud_host/mud_port/mud_username/mud_password properties re-added (see Decisions)
    tool.py                  # unchanged port from 06_the_logger
    message.py               # unchanged port from 06_the_logger
    context.py                # unchanged port from 06_the_logger
    errors.py                # updated — LoopError re-added (see Decisions)
    registry.py               # unchanged port from 06_the_logger
    prompt_builder.py         # unchanged port from 06_the_logger
    client.py                 # unchanged port from 06_the_logger
    logger.py                 # updated — adds turn(), subscribe()
    agent.py                  # unchanged port from 06_the_logger
    run_dsl.py                 # NEW — RunDSL class
    tasks/
      __init__.py
      base.py                # unchanged port from 06_the_logger
      player.py               # unchanged port from 06_the_logger
    backends/
      __init__.py
      base.py                # unchanged port from 06_the_logger
      anthropic.py             # unchanged port from 06_the_logger
      gemini.py                # unchanged port from 06_the_logger
      ollama.py                 # unchanged port from 06_the_logger
      ollama_cloud.py           # unchanged port from 06_the_logger
      openai.py                 # unchanged port from 06_the_logger
  examples/
    example.py                 # rewritten — calls boukensha.run(...) instead of manual wiring

week1_baseline/bin/python/07_the_run_dsl   # new — parallel to bin/python/06_the_logger
```

## Ruby → Python mapping

| Ruby | Python | Notes |
|---|---|---|
| `Boukensha::RunDSL` (new class, `run_dsl.rb`) | `boukensha/run_dsl.py`'s `RunDSL` class | |
| `initialize(registry)` → `@registry = registry` | `__init__(self, registry)` → `self._registry = registry` | |
| `tool(name, description:, parameters: {}, &block)` → `@registry.tool(name, description: description, parameters: parameters, &block)` | `tool(self, name, description, parameters=None, block=None)` → `return self._registry.tool(name, description=description, parameters=parameters or {}, block=block)` | matches `Registry.tool`'s existing Python signature exactly (see `06_the_logger`) — no `&block`/closures to translate, just forwarding a plain callable |
| `Boukensha.quiet!` / `.loud!` / `.quiet?` / `.debug!` / `.debug?` / `.config` | `set_quiet`/`set_loud`/`is_quiet`/`set_debug`/`is_debug`/`get_config` | unchanged from `06_the_logger` |
| `Boukensha.run(task:, system: nil, model: nil, backend: nil, api_key: nil, ollama_host: "http://localhost:11434", log: nil, max_output_tokens: nil, &block)` | `run(task, system=None, model=None, backend=None, api_key=None, ollama_host="http://localhost:11434", log=None, max_output_tokens=None, configure=None)` | module-level function in `boukensha/__init__.py`; `task` positional-or-keyword since Ruby's is a required keyword — Python signature keeps it as the first param, callable as `boukensha.run(task="...")` or `boukensha.run("...")`, matching how prior steps didn't force keyword-only args either |
| `cfg = config` (loads `.env`, populates `ENV`) | `cfg = get_config()` | |
| `task_class = Tasks::Player` | `task_class = Player` (imported from `.tasks.player`) | hardcoded, matching Ruby — no task selection mechanism exists yet |
| `task_settings = cfg.tasks(task_class.task_name)` | `task_settings = cfg.tasks(task_class.task_name())` | `task_name` is a classmethod in both |
| `system ||= task_class.system_prompt(task_settings, user_prompts_dir: cfg.user_prompts_dir, default_prompts_dir: Config::PROMPTS_DIR)` | `system = system or task_class.system_prompt(task_settings, user_prompts_dir=cfg.user_prompts_dir, default_prompts_dir=PROMPTS_DIR)` | `PROMPTS_DIR` imported from `.config` — it's a module-level constant in Python, not a class attribute (established in `00_config`) |
| `model ||= task_class.model(task_settings)` | `model = model or task_class.model(task_settings)` | |
| `backend ||= task_class.provider(task_settings).to_sym` | `backend = backend or task_class.provider(task_settings)` | plain string, no symbol conversion (see Decisions) |
| `api_key ||= case backend when :anthropic then ENV["ANTHROPIC_API_KEY"] when :openai then ENV["OPENAI_API_KEY"] when :gemini then ENV["GEMINI_API_KEY"] when :ollama_cloud then ENV["OLLAMA_API_KEY"] end` | `if api_key is None: api_key = {"anthropic": os.environ.get("ANTHROPIC_API_KEY"), "openai": os.environ.get("OPENAI_API_KEY"), "gemini": os.environ.get("GEMINI_API_KEY"), "ollama_cloud": os.environ.get("OLLAMA_API_KEY")}.get(backend)` | `:ollama` intentionally has no case arm in Ruby (no key needed) — `.get(backend)` returns `None` for `"ollama"` too, same effective behavior |
| `ctx = Context.new(task: task_class, system: system)` | `ctx = Context(task=task_class, system=system)` | |
| `registry = Registry.new(ctx)` | `registry = Registry(ctx)` | |
| `RunDSL.new(registry).instance_eval(&block) if block` | `if configure is not None: configure(RunDSL(registry))` | see Decisions |
| `be = case backend when :anthropic then Backends::Anthropic.new(api_key:, model:) when :openai ... when :gemini ... when :ollama then Backends::Ollama.new(host: ollama_host, model:) when :ollama_cloud ... else raise ArgumentError` | `if backend == "anthropic": be = Anthropic(api_key=api_key, model=model)` / `elif backend == "openai": be = OpenAI(...)` / `elif backend == "gemini": be = Gemini(...)` / `elif backend == "ollama": be = Ollama(model=model, host=ollama_host)` / `elif backend == "ollama_cloud": be = OllamaCloud(...)` / `else: raise ValueError(f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'.")` | `ArgumentError` → `ValueError`, matching the exception-mapping precedent from `00_config`/`03_prompt_builder` |
| `builder = PromptBuilder.new(ctx, be)` / `client = Client.new(builder)` | `builder = PromptBuilder(ctx, be)` / `client = Client(builder)` | |
| `effective_max_iterations = task_class.max_iterations(task_settings)` | `effective_max_iterations = task_class.max_iterations(task_settings)` | |
| `effective_max_output_tokens = max_output_tokens \|\| task_class.max_output_tokens(task_settings)` | `effective_max_output_tokens = max_output_tokens or task_class.max_output_tokens(task_settings)` | |
| `logger = Logger.new(log: log, snapshot: {task: task_class.task_name, max_iterations:, max_output_tokens:, model:, provider: backend})` | `logger = Logger(log=log, snapshot={"task": task_class.task_name(), "max_iterations": effective_max_iterations, "max_output_tokens": effective_max_output_tokens, "model": model, "provider": backend})` | |
| `agent = Agent.new(context: ctx, registry: registry, builder: builder, client: client, logger: logger, task_settings: task_settings, max_iterations: effective_max_iterations, max_output_tokens: effective_max_output_tokens)` | `agent = Agent(ctx, registry, builder, client, logger=logger, task_settings=task_settings, max_iterations=effective_max_iterations, max_output_tokens=effective_max_output_tokens)` | |
| `ctx.add_message(:user, task)` / `agent.run` | `ctx.add_message("user", task)` / `return agent.run()` | inside the `try` |
| `ensure logger&.close` | `finally: logger.close()` | wraps everything from `Logger(...)` construction onward (see Decisions); `logger` is guaranteed non-`None` by this point since `Logger(...)` always succeeds or raises before assignment matters |
| `Logger#turn(n:)` → `write_log(phase: "turn", n: n)` | `Logger.turn(self, n)` → `self._write_log({"phase": "turn", "n": n})` | unused this step (see Decisions) |
| `Logger#subscribe(&block)` → `@subscribers ||= []; @subscribers << block` | `Logger.subscribe(self, callback)` → `self._subscribers.append(callback)` | `self._subscribers = []` initialized in `__init__` (Python has no `\|\|=`-on-first-use idiom as clean as Ruby's, so initialize eagerly instead of lazily — same observable behavior, no `None`-checking needed at call sites) |
| `write_log(event)` → ... `@subscribers&.each { \|s\| s.call(event) }` | `_write_log(self, event)` → ... `for s in self._subscribers: s(event)` | called after the file write+flush, with the same `event` dict passed to `_write_log` (pre-`session_id`/`at` merge — matches Ruby, which iterates subscribers over the local `event` var, not the merged one written to disk) |
| `Boukensha::LoopError < StandardError` | `class LoopError(Exception): pass` | re-added (see Decisions) |
| `Config#mud_host` → `dig(:mud, :host) \|\| "localhost"` | `Config.mud_host` (`@property`) → `self.dig("mud", "host") or "localhost"` | re-added (see Decisions) |
| `Config#mud_port` → `dig(:mud, :port) \|\| 4000` | `Config.mud_port` (`@property`) → `self.dig("mud", "port") or 4000` | re-added |
| `Config#mud_username` → `dig(:mud, :username)` | `Config.mud_username` (`@property`) → `self.dig("mud", "username")` | re-added |
| `Config#mud_password` → `dig(:mud, :password)` | `Config.mud_password` (`@property`) → `self.dig("mud", "password")` | re-added |

## Config directory resolution (unchanged)

Same as `06_the_logger`: `BOUKENSHA_DIR` env var, else `~/.boukensha`,
resolved via `pathlib`. `PROMPTS_DIR` resolution unchanged.
`boukensha.get_config()` continues to back `Logger._default_dir()`; `run()`
calls it too (as `cfg`) for task settings, prompts, and `.env` loading —
same "two independent `Config` instances can coexist" behavior noted in
`06_the_logger`'s plan (here, `run()`'s `cfg` and `Logger`'s internal
`get_config()` call *do* end up being the same memoized instance, since
`get_config()` is called first and cached — unlike `06_the_logger`'s
`example.rb`/`example.py`, which constructed their own separate `Config()`
rather than calling the module accessor).

## Config schema (unchanged)

No new `settings.yaml` keys. Same `tasks.player.{provider,model,
prompt_override,max_iterations,max_output_tokens}` shape as `06_the_logger`.
The `mud:` block in `.boukensha/settings.yaml` is now read by the re-added
`mud_*` properties' `dig()` calls if anything ever calls them — still
nothing does in this step.

## Verified Ruby output

Captured by running `./week1_baseline/bin/ruby/07_the_run_dsl` for real
against the repo's `.boukensha/` directory and a live Anthropic API key
(provider `anthropic`, model `claude-haiku-4-5`). Stdout:

```
=== BOUKENSHA Step 7: The Boukensha.run DSL ===

Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>


=== FINAL RESPONSE ===
## Summary

This MUD player assistant framework (called **Boukensha**) is a Ruby-based system that enables building intelligent agents to interact with MUDs (Multi-User Dungeons). Here's what it can do:
...
(2 iterations, 1 tool call: read_file README.md)
```

And the corresponding session file written to
`.boukensha/sessions/<session-id>.jsonl` — one JSON object per line, in call
order. First and a representative middle line, pretty-printed here for
readability (the real file is one compact JSON object per line):

```json
{"phase":"session_start","task":"player","max_iterations":25,"max_output_tokens":1024,"model":"claude-haiku-4-5","provider":"anthropic","session_id":"20260809T222914Z-4936135f","at":"2026-08-09T18:29:14-04:00"}
{"phase":"iteration","n":1,"max":25,"session_id":"20260809T222914Z-4936135f","at":"2026-08-09T18:29:14-04:00"}
{"phase":"prompt","message_count":1,"messages":[{"role":"user","content":"Read the README.md file and summarise what this MUD player assistant framework can do."}],"tool_count":2,"tools":["read_file","list_directory"],"session_id":"20260809T222914Z-4936135f","at":"2026-08-09T18:29:14-04:00"}
{"phase":"response","text":"(tool use — 1 call)","usage":{"input_tokens":703,"...":"..."},"stop_reason":"tool_use","task":"player","provider":"anthropic","model":"claude-haiku-4-5","usage_unit":"tokens","input_tokens":703,"output_tokens":56,"cost_usd":0.000983,"session_id":"20260809T222914Z-4936135f","at":"2026-08-09T18:29:15-04:00"}
{"phase":"tool_call","name":"read_file","args":{"path":"README.md"},"session_id":"20260809T222914Z-4936135f","at":"2026-08-09T18:29:15-04:00"}
{"phase":"tool_result","name":"read_file","result":"# Step 6 — The Boukensha.run DSL\n...","ok":true,"error":null,"session_id":"20260809T222914Z-4936135f","at":"2026-08-09T18:29:15-04:00"}
...
{"phase":"turn_end","reason":"completed","iterations":2,"tokens":null,"session_id":"20260809T222914Z-4936135f","at":"2026-08-09T18:29:19-04:00"}
```

Key shape confirmation versus `06_the_logger`: `session_start` now carries
the five `snapshot` fields (`task`, `max_iterations`, `max_output_tokens`,
`model`, `provider`) merged in before `session_id`/`at` — bare in
`06_the_logger`, populated here because `run_dsl.rb` is the first caller to
pass a non-empty `snapshot:`. As with prior steps, the model's actual tool
choice, iteration count, and generated text are non-deterministic — this is
the source of truth for **shape** (stdout's labeled lines and blank-line
spacing; `session_start`'s new snapshot fields; every other event's `phase`
and field set unchanged from `06_the_logger`), not for exact text or exact
iteration count.

## Implementation steps

1. **Scaffold** `week1_baseline/python/07_the_run_dsl/` per the layout
   above; copy `requirements.txt` from `06_the_logger` unchanged.
2. **`boukensha/tool.py`, `boukensha/message.py`, `boukensha/context.py`,
   `boukensha/registry.py`, `boukensha/prompt_builder.py`,
   `boukensha/client.py`, `boukensha/agent.py`, `boukensha/tasks/base.py`,
   `boukensha/tasks/player.py`, `boukensha/backends/*.py`** — copy unchanged
   from `06_the_logger`.
3. **`prompts/system.md`** — copy unchanged from `06_the_logger`.
4. **`boukensha/errors.py`** — copy from `06_the_logger`, re-add
   `class LoopError(Exception): pass` (see Decisions).
5. **`boukensha/config.py`** — copy from `06_the_logger`, re-add the
   `mud_host`/`mud_port`/`mud_username`/`mud_password` `@property` methods
   (see Decisions), same bodies as they had before `06_the_logger` removed
   them.
6. **`boukensha/logger.py`** — copy from `06_the_logger`, add `turn(self, n)`
   and `subscribe(self, callback)` per the mapping table; initialize
   `self._subscribers = []` in `__init__`; add the subscriber-notification
   loop at the end of `_write_log`.
7. **`boukensha/run_dsl.py`** — new `RunDSL` class per the mapping table:
   `__init__(self, registry)`, `tool(self, name, description, parameters=None, block=None)`.
8. **`boukensha/__init__.py`** — add the module-level `run` function per the
   mapping table (imports `Player` from `.tasks.player`, `PROMPTS_DIR` from
   `.config`, `RunDSL` from `.run_dsl`, `Context`/`Registry`/`PromptBuilder`/
   `Client`/`Logger`/`Agent`/backend classes — all already importable from
   this same file's existing top-of-file imports or added alongside them);
   add `RunDSL` to the re-exports; re-add `LoopError` to the re-exports.
   Watch import order the same way `06_the_logger` did for `get_config`:
   `run` depends on names defined via `from .X import Y` lines already
   present in `__init__.py`, so place `run`'s `def` after those imports (or
   do local imports inside the function body) to avoid a circular-import
   error at module load time.
9. **`examples/example.py`** — rewrite per `example.rb`'s diff: drop all the
   manual `Context`/`Registry`/backend-cascade/`PromptBuilder`/`Client`/
   `Logger`/`Agent` construction; keep the header prints (`Config:
   {get_config()}`); define `_read_file(path)`/`_list_directory(path)` at
   module scope (same bodies as `06_the_logger`'s, resolving relative to
   `base_dir = Path(__file__).resolve().parent.parent`); define a
   `_configure(dsl)` function that calls `dsl.tool("read_file", description=...,
   parameters=..., block=_read_file)` and `dsl.tool("list_directory",
   description=..., parameters=..., block=_list_directory)`; call
   `result = boukensha.run(task="Read the README.md file and summarise what
   this MUD player assistant framework can do.", configure=_configure)`;
   print `=== FINAL RESPONSE ===` and `result`, header bumped to `"===
   BOUKENSHA Step 7: The Boukensha.run DSL ==="`.
10. **`week1_baseline/bin/python/07_the_run_dsl`** — new bash script, same
    template as every prior step's entry script:
    ```bash
    #!/usr/bin/env bash

    cd "$(dirname "$0")/../../python/07_the_run_dsl"
    source .venv/bin/activate
    python examples/example.py
    ```
    (`chmod +x`).
11. **`README.md`** in `python/07_the_run_dsl/` — same section shape as
    Ruby's (`What this step adds`, `The new primitive` covering both
    `RunDSL` and `run`, `Before and after` using this port's own
    `06_the_logger`-vs-`07_the_run_dsl` Python snippets, `Run Example`),
    with a corrected `run()` options table listing the actual parameters
    (`task`, `system`, `model`, `backend`, `api_key`, `ollama_host`, `log`,
    `max_output_tokens`, `configure`) and their real defaults (see
    Decisions) instead of Ruby's stale `token_budget:`/`max_tokens:`/
    hardcoded-default table.
12. **Verify**: run `./week1_baseline/bin/python/07_the_run_dsl` for real and
    confirm stdout matches "Verified Ruby output" above (header text,
    blank-line spacing, `=== FINAL RESPONSE ===`) and that a new `.jsonl`
    file appears under `.boukensha/sessions/` with `session_start` carrying
    the five snapshot fields (`task`, `max_iterations`, `max_output_tokens`,
    `model`, `provider`) before `session_id`/`at`, and `turn_end` as its
    last line. Also smoke-test paths the happy run doesn't reach:
    - Call `run(task=..., configure=None)` (or omit `configure` entirely)
      and confirm it works with zero tools registered.
    - Call `logger.turn(n=1)` and `logger.subscribe(callback)` directly
      against a `Logger` instance and confirm they behave per the mapping
      table (a subscribed callback receives the pre-`session_id`/`at`
      event dict for every subsequent `_write_log` call, including one
      triggered by `turn`).
    - Pass an unknown `backend="bogus"` and confirm `run()` raises
      `ValueError` with the same message shape as Ruby's `ArgumentError`.
    - Confirm `logger.close()` is actually called on both the success path
      and when `agent.run()` raises — e.g. wrap a call in
      `pytest.raises`-style manual try/except (no test suite exists, so do
      this as an ad hoc script) and check `logger._log_io.closed` is
      `True` afterward either way.

## Out of scope for this step

- No MUD connection / no actual `look`/`move` gameplay tools — the example
  still uses the filesystem tools (`read_file`, `list_directory`)
  introduced in `04_api_client`, per Ruby's own `example.rb`. The re-added
  `mud_*` Config properties stay unused (see Decisions).
- No task selection — `run()` hardcodes `Tasks::Player`/`Player`, matching
  Ruby; no mechanism to choose a different task class exists yet.
- No use of `Logger.turn`/`Logger.subscribe` by any production code path —
  both exist per Ruby's `logger.rb` but nothing in `run_dsl.rb`, `agent.rb`,
  or `example.py` calls them (see Decisions); verification exercises them
  directly rather than through a real run.
- No new config keys beyond the re-added (still-unread-by-`run()`) `mud:`
  block — `run()`'s overrides (`system`/`model`/`backend`/`api_key`/
  `ollama_host`/`log`/`max_output_tokens`) are constructor kwargs only.
- No `pyproject.toml`/packaging, no CLI entry-point registration, no test
  suite, no third-party dependency — per precedent from every prior step.
- No fixes to rough edges already carried over from `00_config`/
  `01_struct_skeleton`/`02_the_registry`/`03_prompt_builder`/`04_api_client`/
  `05_agent_loop`/`06_the_logger` (`.yml` extension question,
  missing-settings-file handling, `Context`/`Registry`'s dual ownership of
  tools, Ollama's hardcoded local address, `Client` not being fully
  stateless).
- `quiet!`/`loud!`/`quiet?` (`set_quiet`/`set_loud`/`is_quiet`) stay
  defined-but-unused, matching Ruby and carried over from `06_the_logger`.
</content>
