# Python Port Plan · 08_the_repl_loop

Port `week1_baseline/ruby/08_the_repl_loop` to `week1_baseline/python/08_the_repl_loop`,
preserving behavior and output shape exactly. This step adds `Boukensha::Repl`,
an interactive session loop, and a new top-level entry point `Boukensha.repl`
that wires up the same primitives as `Boukensha.run` (`06_the_logger`/
`07_the_run_dsl`) but stays alive across multiple turns instead of returning
after one: it prints a startup banner, reads a line from stdin, dispatches
built-in `/`-commands or runs the agent on it, prints the reply, and loops
back — sharing one `Context` (and therefore one accumulating conversation
history) across every turn. It also fixes a latent bug from `06_the_logger`/
`07_the_run_dsl`: the final assistant reply is now persisted into the
context (previously returned but discarded), a small `Config` resolution
change (a `.boukensha` directory in the current working directory is now
checked before falling back to `~/.boukensha`), a `Client` improvement (401
responses get a clearer error message), and a first `VERSION` constant. It's
a straight port of the current step only: no MUD connection wiring, no fix
for the two rough edges Ruby's own README flags as known-but-deliberately-
unfixed (constructing a fresh `Agent` every turn instead of once; whether
`/quiet`/`/loud` do anything beyond toggle an unread flag) — no scope creep
into future steps' concerns.

Confirmed via `diff -rq` against `07_the_run_dsl`: the only Ruby-side changes
are two new files (`lib/boukensha/repl.rb` — the `Repl` class — and
`lib/boukensha/version.rb` — `VERSION = "0.8.0"`), and five modified files:
`boukensha.rb` (adds `require_relative "boukensha/version"` up top, trims
`self.run`'s doc comment down to one line — "see step 6" — since the full
option docs live in the `07_the_run_dsl` plan already, adds `self.repl`, adds
`require_relative "boukensha/repl"` at the bottom), `agent.rb` (adds
`@context.add_message(:assistant, text)` — or the fallback `msg` — in the
three places `run`/`wrap_up` return final text), `client.rb` (adds a
dedicated 401 error message), `config.rb` (`resolve_dir` gains a cwd-`.boukensha`
check between the env-var override and the `~/.boukensha` default), and
`context.rb` (adds `clear_messages!`). `tool.rb`, `message.rb`, `errors.rb`,
`registry.rb`, `prompt_builder.rb`, `logger.rb`, `run_dsl.rb`,
`tasks/base.rb`, `tasks/player.rb`, all `backends/*.rb` are byte-identical to
`07_the_run_dsl` — copy the Python versions forward unchanged. `examples/example.rb`
and `README.md` are rewritten for this step.

## Decisions (confirmed with user)

- **Per-turn `Agent` construction: carried over unchanged, not fixed.**
  Ruby's own `08_the_repl_loop/README.md` "Technical Considerations" section
  explicitly flags "It looks like REPL loop we initialize on every turn an
  agent. It seems like we should initialize only once" as a known issue it is
  *not* fixing yet ("We are not fixing these now to preserve future layers").
  The Python port mirrors this exactly: `Repl._run_turn` constructs a fresh
  `Agent(...)` every call, same as Ruby's `run_turn`. Confirmed with user —
  default to carrying forward, same precedent every prior step used for known
  rough edges.
- **`/quiet` and `/loud`: carried over unchanged, not investigated.** Ruby's
  README also flags "We need to determine if quiet and loud are legacy
  logging or if they actually provide detailed logs" as unresolved. The
  Python port ports `Repl`'s `/quiet` and `/loud` commands as straight calls
  to the already-existing `set_quiet()`/`set_loud()` (from `06_the_logger`) —
  same "defined, unread by anything, questionable effect" status as Ruby.
  Confirmed with user — not investigated or wired up this step.
- **REPL stdin loop → Python's `input()` builtin, not manual `sys.stdin`
  read/flush.** Ruby does `print PROMPT; $stdout.flush; input = $stdin.gets;
  break unless input`. Python's `input(PROMPT)` already writes the prompt to
  stdout and reads one line, raising `EOFError` at true EOF (Ctrl-D) instead
  of returning `nil` — so the loop becomes
  `try: raw = input(PROMPT) except EOFError: break`. No separate
  print/flush call needed; behaviorally equivalent to Ruby's `gets`.
- **`Interrupt` → `KeyboardInterrupt`.** Ruby's `self.repl` wraps the whole
  `Repl.new(...).start` call in `rescue Interrupt; puts "\nInterrupted."`.
  Python's direct equivalent (raised on Ctrl-C, uncaught by default) is
  `KeyboardInterrupt` — same one-line rescue/except shape, same message.
- **`clear_messages!` → `clear_messages`.** Bang stripped per the established
  convention from prior steps (e.g. `validate_model!` → `validate_model` in
  `03_prompt_builder`).
- **`Boukensha::Repl` → `boukensha/repl.py`'s `Repl` class**, plain port, no
  naming collision to resolve (unlike `06_the_logger`'s `quiet!`/`quiet?`
  pair) — `Repl` has no bang/question-mark method names of its own.
- **`Boukensha.repl(&block)` → `boukensha.repl(..., configure=None)`**, same
  shape as `07_the_run_dsl`'s `run`/`configure` precedent: `configure` is an
  optional plain callable taking one positional argument (the `RunDSL`
  instance), called once before backend construction. No new decision needed
  here — this is the same pattern already established, just reused for a
  second entry point.
- **Stale README, same precedent as every prior step
  (`02_the_registry`/`04_api_client`/`05_agent_loop`/`06_the_logger`/
  `07_the_run_dsl`).** Ruby's `08_the_repl_loop/README.md` has several
  inaccuracies confirmed against the real code: it calls this "Step 7" and
  references a `07_the_repl_loop` folder and `examples/step7.rb` (the real
  folder is `08_the_repl_loop`, the real file is `examples/example.rb`, and
  it's the 9th folder — `00` through `08` — i.e. step index 8); its sample
  banner output doesn't match `repl.rb`'s actual banner (real banner includes
  a `config:`/`provider:` line and a version number, the README's sample
  shows neither); and it describes `Logger#turn` as printing a
  `╔══ turn N ══╗` header to the screen, but `logger.rb`/`logger.py`'s `turn`
  method only writes a JSONL log event — it prints nothing (confirmed live,
  see Verified Ruby output below: no such header appears in stdout). This
  plan documents the actual behavior; the Python README does the same
  instead of copying Ruby's stale text.
- Everything else follows the precedent already set by `00_config` through
  `07_the_run_dsl`: self-contained per-step directory (duplicate `boukensha/`
  package rather than import across step directories), plain `venv` +
  `requirements.txt` (no new dependency), no test suite, entry point script
  at `week1_baseline/bin/python/08_the_repl_loop`.

## Target directory layout

```
week1_baseline/python/08_the_repl_loop/
  requirements.txt          # PyYAML, python-dotenv (unchanged)
  README.md                 # same section shape as Ruby's, corrected per Decisions
  prompts/
    system.md                # unchanged content, copied forward from 07_the_run_dsl
  boukensha/
    __init__.py              # adds repl() and Repl export; VERSION re-exported
    version.py                # NEW — VERSION = "0.8.0"
    config.py                # updated — _resolve_dir gains cwd-.boukensha check
    tool.py                  # unchanged port from 07_the_run_dsl
    message.py               # unchanged port from 07_the_run_dsl
    context.py                # updated — adds clear_messages()
    errors.py                # unchanged port from 07_the_run_dsl
    registry.py               # unchanged port from 07_the_run_dsl
    prompt_builder.py         # unchanged port from 07_the_run_dsl
    client.py                 # updated — dedicated 401 error message
    logger.py                 # unchanged port from 07_the_run_dsl (turn()/subscribe() already exist)
    agent.py                  # updated — persists final assistant reply into context
    run_dsl.py                 # unchanged port from 07_the_run_dsl
    repl.py                    # NEW — Repl class
    tasks/
      __init__.py
      base.py                # unchanged port from 07_the_run_dsl
      player.py               # unchanged port from 07_the_run_dsl
    backends/
      __init__.py
      base.py                # unchanged port from 07_the_run_dsl
      anthropic.py             # unchanged port from 07_the_run_dsl
      gemini.py                # unchanged port from 07_the_run_dsl
      ollama.py                 # unchanged port from 07_the_run_dsl
      ollama_cloud.py           # unchanged port from 07_the_run_dsl
      openai.py                 # unchanged port from 07_the_run_dsl
  examples/
    example.py                 # rewritten — calls boukensha.repl(...) instead of boukensha.run(...)

week1_baseline/bin/python/08_the_repl_loop   # new — parallel to bin/python/07_the_run_dsl
```

## Ruby → Python mapping

| Ruby | Python | Notes |
|---|---|---|
| `Boukensha::VERSION = "0.8.0"` (`version.rb`) | `boukensha/version.py`'s `VERSION = "0.8.0"` | first version constant in either port |
| `Boukensha::Repl` (new class, `repl.rb`) | `boukensha/repl.py`'s `Repl` class | |
| `PROMPT = "boukensha> "` | `Repl.PROMPT = "boukensha> "` | class attribute |
| `HELP = <<~HELP ... HELP` | `Repl.HELP = textwrap.dedent("""...""").strip("\n")` | same five-line command list text |
| `initialize(context:, registry:, builder:, client:, logger:, config_dir: nil, provider: nil, model: nil, version: nil, api_key: nil, task_settings: nil, max_iterations: nil, max_output_tokens: nil)` | `Repl.__init__(self, context, registry, builder, client, logger, config_dir=None, provider=None, model=None, version=None, api_key=None, task_settings=None, max_iterations=None, max_output_tokens=None)` | stores each as `self._x`; `self._turn = 0` |
| `start` → `puts banner; loop do ... end` | `start(self)` → `print(self._banner()); while True: ...` | see full body below the table |
| `print PROMPT; $stdout.flush; input = $stdin.gets; break unless input` | `try: raw = input(self.PROMPT) except EOFError: break` | see Decisions |
| `input = input.chomp.strip; next if input.empty?` | `raw = raw.strip(); if not raw: continue` | |
| `case input when "/exit", "/quit" ... when "/help" ... when "/quiet" ... when "/loud" ... when "/clear" ...` | `if raw in ("/exit", "/quit"): ... elif raw == "/help": ... elif raw == "/quiet": ... elif raw == "/loud": ... elif raw == "/clear": ...` | each branch does its effect then `continue`s (Ruby's `next`), except `/exit`/`/quit` which `break`s |
| `Boukensha.quiet!` / `.loud!` | `boukensha.set_quiet()` / `boukensha.set_loud()` | already-existing module functions from `06_the_logger`, imported into `repl.py` |
| `@context.clear_messages!; @turn = 0` | `self._context.clear_messages(); self._turn = 0` | |
| `run_turn(input)` (private, called for non-command lines) | `self._run_turn(raw)` | see full body below the table |
| `banner` (private) → interpolated heredoc with box-drawing chars, `key_status`/`provider_line`/`config_line`/`ver` | `_banner(self)` (private) | same string, same padding math (`" " * (9 - len(ver))`); `key_status = "✗ API key not set" if not self._api_key or not self._api_key.strip() else "✓ API key set"`; `config_exists = self._config_dir and os.path.isdir(self._config_dir)`; `ver = self._version or "?.?.?"` |
| `rescue LoopError => e; puts "\n[error] #{e.message}"` | `except LoopError as e: print(f"\n[error] {e}")` | `LoopError` imported from `.errors`; still never raised anywhere in this step (same "defined for parity" status as `07_the_run_dsl`), but now genuinely reachable via this `except` clause if a future step raises it |
| `rescue ApiError => e; puts "\n[error] API call failed: #{e.message}"` | `except ApiError as e: print(f"\n[error] API call failed: {e}")` | |
| `Boukensha.repl(system: nil, model: nil, backend: nil, api_key: nil, ollama_host: "http://localhost:11434", log: nil, max_output_tokens: nil, &block)` | `repl(system=None, model=None, backend=None, api_key=None, ollama_host="http://localhost:11434", log=None, max_output_tokens=None, configure=None)` | module-level function in `boukensha/__init__.py`, same setup as `run()` through backend construction, then builds a `Repl` and calls `.start()` instead of running the agent directly — see full body below |
| `RunDSL.new(registry).instance_eval(&block) if block` | `if configure is not None: configure(RunDSL(registry))` | identical to `07_the_run_dsl`'s `run()` |
| `Repl.new(context: ctx, registry:, builder:, client:, logger:, task_settings:, max_iterations:, max_output_tokens:, config_dir: cfg.dir, provider: backend, model:, version: VERSION, api_key:).start` | `Repl(ctx, registry, builder, client, logger, config_dir=cfg.dir, provider=backend, model=model, version=VERSION, api_key=api_key, task_settings=task_settings, max_iterations=effective_max_iterations, max_output_tokens=effective_max_output_tokens).start()` | `provider` stays a plain string (`backend`), no `.to_sym` — same as `07_the_run_dsl`'s backend-cascade decision |
| `rescue Interrupt; puts "\nInterrupted."` | `except KeyboardInterrupt: print("\nInterrupted.")` | wraps the `Repl(...).start()` call |
| `ensure logger&.close` | `finally: logger.close()` | same shape as `07_the_run_dsl`'s `run()` |
| `Agent#run` — adds `@context.add_message(:assistant, text)` before `return text` on the non-tool-use branch | `Agent.run(self)` — adds `self._context.add_message("assistant", text)` before `return text` | one-line insertion, same spot as `06_the_logger`'s `_log_response`/`turn_end` calls |
| `Agent#wrap_up` — adds `@context.add_message(:assistant, text)` before the final `text` (success path) and `@context.add_message(:assistant, msg)` before `msg` (rescue `ApiError` path) | `Agent._wrap_up(self)` — adds `self._context.add_message("assistant", text)` / `self._context.add_message("assistant", msg)` in the matching two spots | |
| `Client#call` — `if response.code.to_i == 401; raise ApiError, "authentication failed (401) — check your API key"; end` before the general failure raise | `Client.call(self, ...)` — inside the `except urllib.error.HTTPError as e:` branch, before the generic `raise ApiError(...)`, add `if e.code == 401: raise ApiError("authentication failed (401) — check your API key") from e` | 401 isn't in `RETRYABLE_STATUS_CODES`, so this check only needs to sit ahead of the final non-retryable raise, not inside the retry branch |
| `Config#resolve_dir` — three-step cascade: env var, then cwd `.boukensha` if it's a directory, then `~/.boukensha` | `Config._resolve_dir(self)` — same three-step cascade | `if os.environ.get("BOUKENSHA_DIR"): return str(Path(os.environ["BOUKENSHA_DIR"]).expanduser().resolve())`; `cwd_dir = Path.cwd() / ".boukensha"`; `if cwd_dir.is_dir(): return str(cwd_dir)`; `return str(Path(self.DEFAULT_DIR).expanduser().resolve())` |
| `Context#clear_messages!` → `@messages = []` | `Context.clear_messages(self)` → `self.messages = []` | see Decisions |

### `Repl.start` (full body, Python)

```python
def start(self):
    print(self._banner())

    while True:
        try:
            raw = input(self.PROMPT)
        except EOFError:
            break

        raw = raw.strip()
        if not raw:
            continue

        if raw in ("/exit", "/quit"):
            print("Goodbye.")
            break
        elif raw == "/help":
            print(self.HELP)
            continue
        elif raw == "/quiet":
            set_quiet()
            print("(logging suppressed — type /loud to re-enable)")
            continue
        elif raw == "/loud":
            set_loud()
            print("(logging enabled)")
            continue
        elif raw == "/clear":
            self._context.clear_messages()
            self._turn = 0
            print("(conversation history cleared)")
            continue

        self._run_turn(raw)
```

### `Repl._run_turn` (full body, Python)

```python
def _run_turn(self, raw):
    self._turn += 1
    self._logger.turn(self._turn)

    self._context.add_message("user", raw)

    agent = Agent(
        self._context, self._registry, self._builder, self._client,
        logger=self._logger, task_settings=self._task_settings,
        max_iterations=self._max_iterations, max_output_tokens=self._max_output_tokens,
    )
    try:
        result = agent.run()
    except LoopError as e:
        print(f"\n[error] {e}")
        return
    except ApiError as e:
        print(f"\n[error] API call failed: {e}")
        return

    print()
    print(result)
```

(`Agent`/`LoopError`/`ApiError` imported at the top of `repl.py`, matching
Ruby's `rescue` clauses attached directly to `run_turn`'s body — Python
expresses the same "catch around the whole turn" shape as a `try/except`
around just the `agent.run()` call, since `print`/`add_message` calls before
it can't raise either exception.)

### `boukensha.repl` (full body, Python)

```python
def repl(system=None, model=None, backend=None, api_key=None,
         ollama_host="http://localhost:11434", log=None, max_output_tokens=None,
         configure=None):
    cfg = get_config()
    task_class = Player
    task_settings = cfg.tasks(task_class.task_name())
    system = system or task_class.system_prompt(
        task_settings, user_prompts_dir=cfg.user_prompts_dir, default_prompts_dir=PROMPTS_DIR
    )
    model = model or task_class.model(task_settings)
    backend = backend or task_class.provider(task_settings)
    if api_key is None:
        api_key = {
            "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
            "openai": os.environ.get("OPENAI_API_KEY"),
            "gemini": os.environ.get("GEMINI_API_KEY"),
            "ollama_cloud": os.environ.get("OLLAMA_API_KEY"),
        }.get(backend)

    ctx = Context(task=task_class, system=system)
    registry = Registry(ctx)

    if configure is not None:
        configure(RunDSL(registry))

    if backend == "anthropic":
        be = Anthropic(api_key=api_key, model=model)
    elif backend == "openai":
        be = OpenAI(api_key=api_key, model=model)
    elif backend == "gemini":
        be = Gemini(api_key=api_key, model=model)
    elif backend == "ollama":
        be = Ollama(model=model, host=ollama_host)
    elif backend == "ollama_cloud":
        be = OllamaCloud(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'.")

    builder = PromptBuilder(ctx, be)
    client = Client(builder)
    effective_max_iterations = task_class.max_iterations(task_settings)
    effective_max_output_tokens = max_output_tokens or task_class.max_output_tokens(task_settings)
    logger = Logger(log=log, snapshot={
        "task": task_class.task_name(),
        "max_iterations": effective_max_iterations,
        "max_output_tokens": effective_max_output_tokens,
        "model": model,
        "provider": backend,
    })

    try:
        Repl(
            ctx, registry, builder, client, logger,
            config_dir=cfg.dir, provider=backend, model=model, version=VERSION, api_key=api_key,
            task_settings=task_settings, max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens,
        ).start()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        logger.close()
```

## Config directory resolution (updated)

`BOUKENSHA_DIR` env var (if set) wins outright. Otherwise, a `.boukensha`
directory in the current working directory is used if one exists. Otherwise,
falls back to `~/.boukensha`. `PROMPTS_DIR` resolution is unchanged (always
the package's own bundled `prompts/` directory, independent of this
cascade). This step's own verification run sets `BOUKENSHA_DIR` explicitly
(matching the repo's `bin/ruby/08_the_repl_loop` script), so the new
cwd-check branch isn't exercised by the main run — it needs a dedicated
smoke test (see Implementation steps).

## Config schema (unchanged)

No new `settings.yaml` keys. Same `tasks.player.{provider,model,
prompt_override,max_iterations,max_output_tokens}` shape as `07_the_run_dsl`.

## Verified Ruby output

Captured by running `bundle exec ruby examples/example.rb` for real from
`week1_baseline/ruby/08_the_repl_loop/`, with `BOUKENSHA_DIR` pointed at the
repo's `.boukensha/` directory and a live Anthropic API key (provider
`anthropic`, model `claude-haiku-4-5`), feeding it four scripted lines on
stdin: `/help`, `list the files in the lib directory`,
`what was the first file I asked you about?`, `/exit`. Full stdout:

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
The lib directory contains the following files:

1. **boukensha** (appears to be a directory)
2. **boukensha.rb** (a Ruby file)

Would you like me to explore either of these further?
boukensha> 
The first file you asked me about was the files in the **lib directory**.
boukensha> Goodbye.
```

Note there is no per-turn `╔══ turn N ══╗` header printed anywhere — the
README's claim to that effect is stale (see Decisions); `Logger#turn` only
writes a JSONL event.

And the corresponding session file written to
`.boukensha/sessions/<session-id>.jsonl` — one JSON object per line. First
few lines and the two `"phase":"turn"` lines, pretty-printed here for
readability (the real file is one compact JSON object per line):

```json
{"phase":"session_start","task":"player","max_iterations":25,"max_output_tokens":1024,"model":"claude-haiku-4-5","provider":"anthropic","session_id":"20260810T001424Z-ed5ddede","at":"2026-08-09T20:14:24-04:00"}
{"phase":"turn","n":1,"session_id":"20260810T001424Z-ed5ddede","at":"2026-08-09T20:14:24-04:00"}
{"phase":"iteration","n":1,"max":25,"session_id":"20260810T001424Z-ed5ddede","at":"2026-08-09T20:14:24-04:00"}
...
{"phase":"turn","n":2,"session_id":"20260810T001424Z-ed5ddede","at":"2026-08-09T20:14:25-04:00"}
...
```

Key shape confirmation versus `07_the_run_dsl`: two `"phase":"turn"` events
appear (one per REPL turn, `/help` doesn't count since it's a built-in
command handled before `run_turn`), and turn 2's `"phase":"prompt"` event's
`messages` array carries five entries — including the turn-1 assistant reply
and its tool-call/tool-result pair — confirming conversation history now
persists across turns (this is the `@context.add_message(:assistant, text)`
fix in `agent.rb`; without it, turn 2 would only see the turn-2 user message
and lose the tool-use exchange from turn 1). As with prior steps, the
model's actual tool choice, iteration count, and generated text are
non-deterministic — this is the source of truth for **shape** (banner
layout, prompt/command echo, blank-line spacing, JSONL `phase` values and
field sets, cross-turn `messages` accumulation), not for exact text.

## Implementation steps

1. **Scaffold** `week1_baseline/python/08_the_repl_loop/` per the layout
   above; copy `requirements.txt` from `07_the_run_dsl` unchanged.
2. **`boukensha/tool.py`, `boukensha/message.py`, `boukensha/errors.py`,
   `boukensha/registry.py`, `boukensha/prompt_builder.py`,
   `boukensha/logger.py`, `boukensha/run_dsl.py`, `boukensha/tasks/base.py`,
   `boukensha/tasks/player.py`, `boukensha/backends/*.py`** — copy unchanged
   from `07_the_run_dsl`.
3. **`prompts/system.md`** — copy unchanged from `07_the_run_dsl`.
4. **`boukensha/version.py`** — new file: `VERSION = "0.8.0"`.
5. **`boukensha/context.py`** — copy from `07_the_run_dsl`, add
   `clear_messages(self)` (see mapping table).
6. **`boukensha/client.py`** — copy from `07_the_run_dsl`, add the 401
   special case inside the `HTTPError` except branch, ahead of the generic
   `ApiError` raise (see mapping table).
7. **`boukensha/config.py`** — copy from `07_the_run_dsl`, update
   `_resolve_dir` to the three-step cascade (see mapping table).
8. **`boukensha/agent.py`** — copy from `07_the_run_dsl`, add
   `self._context.add_message("assistant", text)` /
   `self._context.add_message("assistant", msg)` in the three spots
   identified in the mapping table (`run`'s final-return branch, `_wrap_up`'s
   success path, `_wrap_up`'s `except ApiError` path).
9. **`boukensha/repl.py`** — new `Repl` class per the mapping table and the
   full method bodies given above (`__init__`, `start`, `_run_turn`,
   `_banner`). Imports: `os`, `.agent.Agent`, `.errors.ApiError`,
   `.errors.LoopError`, and `set_quiet`/`set_loud` from the package
   `__init__` (deferred/local import inside methods if needed to dodge a
   circular-import cycle with `__init__.py`, same caveat noted in
   `06_the_logger`'s and `07_the_run_dsl`'s implementation steps).
10. **`boukensha/__init__.py`** — add the module-level `repl` function per
    the mapping table (imports `Repl` from `.repl`, `VERSION` from
    `.version`; reuses the same `Player`/`PROMPTS_DIR`/`Context`/`Registry`/
    `RunDSL`/backend classes/`PromptBuilder`/`Client`/`Logger` imports
    already present from wiring up `run()`); add `Repl` and `VERSION` to the
    re-exports. Watch import order the same way `06_the_logger`/
    `07_the_run_dsl` did: place `repl`'s `def` after the relevant `from .X
    import Y` lines, or use local imports inside the function body, to avoid
    a circular-import error at module load time.
11. **`examples/example.py`** — rewrite per `example.rb`'s diff: keep the
    header print (`Config: {get_config()}`); `base_dir` points at the
    sibling `../../07_the_run_dsl` Python step directory (mirroring Ruby's
    own sibling-folder reference, adjusted to the Python tree); define
    `_read_file(path)`/`_list_directory(path)` at module scope (same bodies
    as `07_the_run_dsl`'s, resolving relative to `base_dir`); define
    `_configure(dsl)` registering `read_file`/`list_directory` exactly as
    `07_the_run_dsl`'s `_configure` did; call `boukensha.repl(configure=_configure)`
    with no other arguments (matching Ruby's `Boukensha.repl do ... end`,
    which passes no keyword overrides either).
12. **`week1_baseline/bin/python/08_the_repl_loop`** — new bash script, same
    template as every prior step's entry script:
    ```bash
    #!/usr/bin/env bash

    cd "$(dirname "$0")/../../python/08_the_repl_loop"
    source .venv/bin/activate
    python examples/example.py
    ```
    (`chmod +x`).
13. **`README.md`** in `python/08_the_repl_loop/` — same section shape as
    Ruby's (`What this step adds`, `New primitives` covering `Repl` and
    `Boukensha.repl`, `Changes from step 7` covering `clear_messages`/the
    persisted-assistant-reply fix/the 401 message/the cwd config lookup,
    `Running it` with this port's own live transcript and banner, `Technical
    Considerations` carrying the same two open questions forward per
    Decisions), with the step numbering, folder name, and file name
    corrected to `08_the_repl_loop`/`example.py`, and the `Logger#turn`
    description corrected to say it writes a log event rather than printing
    a header (see Decisions).
14. **Verify**: run `./week1_baseline/bin/python/08_the_repl_loop`, feeding
    it the same four scripted lines (`/help`, `list the files in the lib
    directory`, `what was the first file I asked you about?`, `/exit`) via
    stdin, and confirm stdout matches "Verified Ruby output" above (banner
    layout including the padded version line, command echo for `/help`,
    blank-line spacing, `Goodbye.`) and that a new `.jsonl` file appears
    under `.boukensha/sessions/` with two `"phase":"turn"` events and turn
    2's `"phase":"prompt"` event carrying the accumulated 5-message history
    (confirming the persisted-assistant-reply fix). Also smoke-test paths
    the happy run doesn't reach:
    - Feed `/quiet` then a task, then `/loud`, and confirm both commands
      print their confirmation lines and don't crash (their effect on
      logging output is intentionally left unverified — see Decisions).
    - Feed `/clear` mid-conversation and confirm the next turn's `"prompt"`
      log event's `message_count` resets to reflect only the post-clear
      messages, not the pre-clear history.
    - Send Ctrl-D (EOF) with no trailing `/exit` and confirm the REPL exits
      the loop cleanly without printing `Goodbye.` (matching Ruby's `break
      unless input` — EOF is a silent exit, not a `/exit`-triggered one).
    - Construct a `Config` with `BOUKENSHA_DIR` unset and the current working
      directory holding a `.boukensha/` subdirectory; confirm `Config().dir`
      resolves to that cwd directory rather than `~/.boukensha` (the new
      cascade step, unexercised by the main scripted run since it sets
      `BOUKENSHA_DIR` explicitly).
    - Point at a backend/API key combination that returns 401 (or construct
      a fake `urllib.error.HTTPError` with `code=401` directly against
      `Client._retry_delay`'s call site) and confirm the raised `ApiError`
      message is exactly `"authentication failed (401) — check your API
      key"`, not the generic attempt-count message.

## Out of scope for this step

- No MUD connection / no actual `look`/`move` gameplay tools — the example
  still uses the filesystem tools (`read_file`, `list_directory`)
  introduced in `04_api_client`, per Ruby's own `example.rb`.
- No fix for constructing a fresh `Agent` on every REPL turn instead of once
  — carried over unchanged per Ruby's own README and this plan's Decisions.
- No fix or investigation of whether `/quiet`/`/loud` (`set_quiet`/
  `set_loud`) have any real effect on logging output — carried over
  unchanged per Ruby's own README and this plan's Decisions.
- No task selection — `repl()` hardcodes `Tasks::Player`/`Player`, matching
  Ruby and matching `07_the_run_dsl`'s `run()`.
- No readline-style history/editing beyond whatever the underlying terminal
  and Python's `input()` provide for free — no explicit `readline` module
  wiring, matching Ruby's plain `$stdin.gets` (no `Readline` library used
  there either).
- No `pyproject.toml`/packaging, no CLI entry-point registration, no test
  suite, no third-party dependency — per precedent from every prior step.
- No fixes to rough edges already carried over from `00_config`/
  `01_struct_skeleton`/`02_the_registry`/`03_prompt_builder`/`04_api_client`/
  `05_agent_loop`/`06_the_logger`/`07_the_run_dsl` (`.yml` extension
  question, missing-settings-file handling, `Context`/`Registry`'s dual
  ownership of tools, Ollama's hardcoded local address, `Client` not being
  fully stateless, `Logger.turn`/`Logger.subscribe` still unused by any
  production code path beyond this step's new `Repl.turn` call).
- No use of `Logger.subscribe` by any production code path — still exists
  per `07_the_run_dsl`'s port but nothing in `repl.py`/`example.py` calls it.

