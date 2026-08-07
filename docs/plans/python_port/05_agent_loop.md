# Python Port Plan · 05_agent_loop

Port `week1_baseline/ruby/05_agent_loop` to `week1_baseline/python/05_agent_loop`,
preserving behavior and output shape exactly. This step adds `Agent`, the
tool-call loop that ties `Client`, `PromptBuilder`, and `Registry` together:
it sends requests, normalizes each backend's response into a common
`{stop_reason, content}` shape via a new `parse_response` on every backend,
dispatches tool calls, replays results back into the conversation, and
wind-down-calls the model once an iteration ceiling is hit. It's a straight
port of the current step only: no MUD connection wiring, no logging/cost
tracking beyond what `Base#estimate_cost` already exposes, no fixes to known
rough edges already carried over from earlier steps (beyond the one bug
below, which is new to this step, not carried over).

Confirmed via `diff -r` against `04_api_client`: the only Ruby-side changes
are a new `lib/boukensha/agent.rb`, a new `prompts/system.md` (same file,
just present because it's now shipped per-step like every prior step),
`errors.rb` (new unused `LoopError`), `config.rb` (endless-method syntax
changes + a `PROMPTS_DIR` path bug, see Decisions), `tasks/base.rb` (new
`max_iterations`/`max_output_tokens` class methods), `prompt_builder.rb`
(new `parse_response`, `tools:` threaded through `to_api_payload`),
`client.rb` (`tools:` threaded through `call`), all five `backends/*.rb`
(new `parse_response`, `tools:` threaded through `to_payload`; `ollama.rb`/
`ollama_cloud.rb`/`openai.rb` also gain a private `assistant_message`
helper and an `:assistant` branch in `to_messages`; `gemini.rb` gains
`assistant_parts` instead), and a rewritten `examples/example.rb`.
`tool.rb`, `message.rb`, `context.rb`, `registry.rb`, `backends/base.rb`,
`tasks/player.rb` are byte-identical to `04_api_client` — copy the Python
versions forward unchanged.

## Decisions (confirmed with user)

- **`PROMPTS_DIR` path bug: fixed, not replicated.** Ruby's `config.rb`
  changes `PROMPTS_DIR` from `File.expand_path("../../prompts", __dir__)`
  to `File.expand_path("../../../prompts", __dir__)` — one `../` too many.
  Verified live (`ruby -e 'require_relative "lib/boukensha/config"; puts
  Boukensha::Config::PROMPTS_DIR'`): it resolves to
  `week1_baseline/ruby/prompts`, a directory that does not exist, instead of
  `week1_baseline/ruby/05_agent_loop/prompts`. This is currently masked in
  this repo because `.boukensha/settings.yaml` has
  `tasks.player.prompt_override.system: true` pointing at
  `.boukensha/prompts/player/system.md`, which exists — so the broken
  default-prompt fallback path is never actually exercised end-to-end.
  If `prompt_override.system` were off, `Tasks::Base.read_default_prompt`
  would silently return `nil` (its `File.exist?` guard just fails closed)
  and the agent would run with `system: nil`. Per user decision, the Python
  port's `PROMPTS_DIR` uses the correct two-level-up expression, matching
  every prior step's pattern (`(Path(__file__).resolve().parent.parent /
  "prompts").resolve()`), not Ruby's three-level-up typo.
- **`LoopError`: ported but intentionally unused.** Ruby's `errors.rb` adds
  `class LoopError < StandardError; end` and the README credits it as
  "Added `LoopError` for runaway agents," but nothing in `agent.rb` (or
  anywhere else in the Ruby step) actually raises it — the iteration ceiling
  is enforced entirely through `wrap_up`, never an exception. The Python
  port adds `class LoopError(Exception): pass` alongside the other error
  classes for parity, but nothing raises it either — straight port of
  Ruby's (apparently forward-looking, currently dead) code, not a bug to
  fix by wiring it up early.
- **Stale README tables, same precedent as `02_the_registry`/`04_api_client`.**
  Ruby's `05_agent_loop/README.md` "New Files" table lists
  `backends/base.rb`, `tasks/base.rb`, `tasks/player.rb`,
  `backends/openai.rb`, `backends/gemini.rb`, `backends/ollama_cloud.rb`,
  and `prompts/system.md` as new, and "Updated Files" credits `context.rb`
  ("carries the active task object") and `config.rb` ("reads tasks.player
  instead of top-level settings") as changing in this step — none of that is
  true for this diff (`diff -rq` against `04_api_client` shows those files
  either unchanged or, for `config.rb`, changed only in the ways captured
  above). All of that functionality already existed as of `00_config`
  through `03_prompt_builder`. This plan documents the actual diff-verified
  changes instead; the Python README does the same.
- Everything else follows the precedent already set by `00_config` through
  `04_api_client`: self-contained per-step directory (duplicate
  `boukensha/` package rather than import across step directories), plain
  `venv` + `requirements.txt`, stdlib-only HTTP (no new dependency needed —
  this step adds no networking beyond what `Client` already does), no test
  suite, entry point script at `week1_baseline/bin/python/05_agent_loop`.

## Target directory layout

```
week1_baseline/python/05_agent_loop/
  requirements.txt          # PyYAML, python-dotenv (unchanged)
  README.md                 # same shape as Ruby's, New/Updated Files reflect actual diff (see Decisions)
  prompts/
    system.md                # unchanged content, copied forward from 04_api_client
  boukensha/
    __init__.py              # re-exports adds Agent, LoopError
    config.py                # unchanged port from 04_api_client (PROMPTS_DIR already correct — see Decisions)
    tool.py                  # unchanged port from 04_api_client
    message.py               # unchanged port from 04_api_client
    context.py                # unchanged port from 04_api_client
    errors.py                # adds LoopError alongside ApiError, UnknownToolError, UnsupportedModelError
    registry.py               # unchanged port from 04_api_client
    prompt_builder.py         # updated — parse_response, tools param on to_api_payload
    client.py                 # updated — tools param threaded through call()
    agent.py                  # NEW — Agent class, the tool-call loop
    tasks/
      __init__.py
      base.py                # adds max_iterations, max_output_tokens classmethods
      player.py               # unchanged port from 04_api_client
    backends/
      __init__.py
      base.py                # unchanged port from 04_api_client
      anthropic.py            # adds parse_response, tools param on to_payload
      gemini.py                # adds parse_response, _assistant_parts, tools param, assistant branch in to_messages
      ollama.py                 # adds parse_response, _assistant_message, tools param, assistant branch in to_messages
      ollama_cloud.py           # adds parse_response, _assistant_message, tools param, assistant branch in to_messages
      openai.py                 # adds parse_response, _assistant_message, tools param, assistant branch in to_messages
  examples/
    example.py                 # rewritten — read_file/list_directory resolved against step dir, builds and runs Agent

week1_baseline/bin/python/05_agent_loop   # new — parallel to bin/python/04_api_client
```

## Ruby → Python mapping

| Ruby | Python | Notes |
|---|---|---|
| `Boukensha::LoopError < StandardError` | `class LoopError(Exception)` | same treatment as the other error classes; unused in both languages (see Decisions) |
| `Tasks::Base::DEFAULT_MAX_ITERATIONS = 25` / `DEFAULT_MAX_OUTPUT_TOKENS = 1024` | `Base.DEFAULT_MAX_ITERATIONS = 25` / `Base.DEFAULT_MAX_OUTPUT_TOKENS = 1024` | class attributes on `tasks/base.py`'s `Base` |
| `Tasks::Base.max_iterations(settings)` / `.max_output_tokens(settings)` | `Base.max_iterations(cls, settings)` / `Base.max_output_tokens(cls, settings)` classmethods | delegate to a new private `integer_setting(settings, key, default)`; `Integer(value)` → Python `int(value)` |
| `fetch(settings, key)` (existing private helper) | existing `_fetch(settings, key)` | unchanged, reused by `integer_setting` |
| `Client#call(max_output_tokens: 1024, tools: nil)` | `Client.call(self, max_output_tokens=1024, tools=None)` | payload build becomes `self.builder.to_api_payload(max_output_tokens=max_output_tokens, tools=tools)`; retry/backoff loop itself is unchanged from `04_api_client` |
| `PromptBuilder#to_api_payload(max_output_tokens: 1024, tools: nil)` | `to_api_payload(self, max_output_tokens=1024, tools=None)` | delegates to `self.backend.to_payload(self.context, max_output_tokens=max_output_tokens, tools=tools)` |
| `PromptBuilder#parse_response(response)` | `parse_response(self, response)` | `return self.backend.parse_response(response)` |
| Each backend's `to_payload(context, max_output_tokens: 1024, tools: nil)` — `tools.nil? ? to_tools(context.tools) : tools` | `to_payload(self, context, max_output_tokens=1024, tools=None)` — `tools if tools is not None else self.to_tools(context.tools)` | same "explicit `[]` disables tools, `None`/absent uses the context's tools" semantics across all 5 backends |
| `Anthropic#parse_response(response)` | `Anthropic.parse_response(self, response)` | `stop_reason = "tool_use" if response.get("stop_reason") == "tool_use" else "end_turn"`; `return {"stop_reason": stop_reason, "content": response.get("content") or []}` |
| Anthropic's `content` array | same | doubles as both the normalized shape and the wire format — no reverse conversion needed, matching Ruby (per the README's own note, carried into the Python README) |
| `Gemini#parse_response(response)` | `Gemini.parse_response(self, response)` | walk `response.get("candidates", [{}])[0].get("content", {}).get("parts", [])`; `functionCall` → `{"type": "tool_use", "id": fc["name"], "name": fc["name"], "input": fc.get("args") or {}}` (name reused as id — Gemini has no call ids); `text` → `{"type": "text", "text": part["text"]}` |
| `Gemini#assistant_parts(content)` (private) | `Gemini._assistant_parts(self, content)` | inverse of `parse_response`: wraps a bare string as one text block; maps `tool_use` blocks back to `{"functionCall": {"name": ..., "args": ...}}`, text blocks to `{"text": ...}` |
| Gemini `to_messages`, `:assistant` branch: `{ role: "model", parts: [{ text: msg.content }] }` → `{ role: "model", parts: assistant_parts(msg.content) }` | `{"role": "model", "parts": self._assistant_parts(msg.content)}` | |
| `Ollama#parse_response(response)` / `OllamaCloud#parse_response(response)` | `Ollama.parse_response` / `OllamaCloud.parse_response` (identical body in both, matching Ruby duplicating the same method in both classes rather than sharing it via `Base`) | `message = response.get("message") or {}`; text block appended only if `message.get("content")` is non-empty; each `tool_calls` entry → `{"type": "tool_use", "id": fn["name"], "name": fn["name"], "input": fn.get("arguments") or {}}` (name reused as id); `stop_reason` is `"end_turn"` if no tool calls else `"tool_use"` |
| `Ollama#assistant_message(content)` / `OllamaCloud#assistant_message(content)` (private) | `Ollama._assistant_message` / `OllamaCloud._assistant_message` | inverse of `parse_response`: joins text blocks' text, sets `tool_calls` key only if tool blocks are present, each as `{"function": {"name": ..., "arguments": b["input"]}}` (arguments stay a dict, not JSON-encoded — Ollama's wire format takes the object directly, unlike OpenAI) |
| Ollama/OllamaCloud `to_messages`, new `:assistant` branch | `elif msg.role == "assistant": conversation.append(self._assistant_message(msg.content))` | inserted before the trailing `else` that handles all other roles |
| `OpenAI#parse_response(response)` (`require "json"` added for `JSON.parse`) | `OpenAI.parse_response(self, response)` (`import json` at module top) | `message = response.get("choices", [{}])[0].get("message") or {}`; text block appended if `message.get("content")` truthy; each `tool_calls` entry → `{"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"], "input": json.loads(tc["function"].get("arguments") or "{}")}` (OpenAI *does* assign real ids, no reuse-name-as-id needed here) |
| `OpenAI#assistant_message(content)` (private) | `OpenAI._assistant_message` | joins text blocks; `tool_calls` key set only if tool blocks present, each as `{"id": b["id"], "type": "function", "function": {"name": b["name"], "arguments": json.dumps(b["input"])}}` — arguments *are* JSON-encoded here, matching OpenAI's wire format (unlike Ollama) |
| OpenAI/`to_messages`, new `:assistant` branch | same shape as Ollama's | |
| `Boukensha::Agent` (new class) | `boukensha/agent.py`'s `Agent` class | see dedicated mapping rows below |
| `Agent::MAX_ITERATIONS = 25` / `WRAP_UP_OUTPUT_TOKENS = 400` | `Agent.MAX_ITERATIONS = 25` / `Agent.WRAP_UP_OUTPUT_TOKENS = 400` | class attributes; note `MAX_ITERATIONS` here duplicates `Tasks::Base::DEFAULT_MAX_ITERATIONS`'s value (both 25) — that's Ruby's own redundancy (fallback-of-a-fallback), ported as-is, not deduplicated |
| `WRAP_UP_DIRECTIVE = <<~MSG.strip ... MSG` (heredoc) | `WRAP_UP_DIRECTIVE = ("You have reached your action limit for this turn. Do not call any more tools. " "Briefly summarize what you accomplished, what is still unfinished, and the " "single next action you would take.")` | Python has no heredoc; a parenthesized string-literal concatenation reproduces the exact wrapped text, single-spaced, no line breaks (matching Ruby's `<<~MSG.strip` squiggly-heredoc + strip, which folds the multi-line source into one line with single spaces) |
| `initialize(context:, registry:, builder:, client:, task_settings: nil, max_iterations: nil, max_output_tokens: nil)` | `Agent.__init__(self, context, registry, builder, client, task_settings=None, max_iterations=None, max_output_tokens=None)` | Ruby's kwargs-only init becomes plain/keyword-capable Python params, matching how every other ported class already handles this (e.g. `Client.__init__(self, builder)`) |
| `run` — `loop do ... end`, `return wrap_up("max_iterations") if iteration_limit_reached?`, increments `@iteration`, calls, parses, branches on `stop_reason` | `run(self)` — `while True:` loop with the same ordering: check-then-return, increment, call, parse, branch | `if parsed["stop_reason"] == "tool_use": self._handle_tool_calls(parsed["content"])` / `else: return self._extract_text(parsed["content"])` |
| `resolve_max_iterations(task_settings, explicit)` (private) | `_resolve_max_iterations(self, task_settings, explicit)` | `if explicit is not None: return int(explicit)`; `if task_settings and hasattr(self._context.task, "max_iterations"): return self._context.task.max_iterations(task_settings)`; else `return self.MAX_ITERATIONS` — Ruby's `respond_to?(:max_iterations)` duck-type check becomes `hasattr`, same fallback chain |
| `resolve_max_output_tokens(task_settings, explicit)` (private) | `_resolve_max_output_tokens(self, task_settings, explicit)` | same shape, falls back to `None` (not a numeric default) if neither `explicit` nor the task settings supply one — matching Ruby exactly |
| `iteration_limit_reached?` (private) | `_iteration_limit_reached(self)` | `self._max_iterations > 0 and self._iteration >= self._max_iterations` — `0` (or an unset ceiling) disables the check, same as Ruby's `.positive?` guard |
| `call_opts` (private) | `_call_opts(self)` | `{"max_output_tokens": self._max_output_tokens} if self._max_output_tokens else {}`, splatted into `self._client.call(**self._call_opts())` at the call site |
| `wrap_up(reason)` (private) | `_wrap_up(self, reason)` | `self._context.add_message("user", self.WRAP_UP_DIRECTIVE)`; `response = self._client.call(tools=[], max_output_tokens=self.WRAP_UP_OUTPUT_TOKENS)`; `text = self._extract_text(self._builder.parse_response(response)["content"])`; `return text if text.strip() else self._fallback_message(reason)`; wrapped in `try/except ApiError: return self._fallback_message(reason)` — runs outside the counted loop exactly like Ruby (never re-checks the limit, never increments `_iteration`) |
| `fallback_message(reason)` (private) | `_fallback_message(self, reason)` | same f-string, same wording |
| `extract_text(content)` (private) | `_extract_text(self, content)` | `"".join(b["text"] for b in content if b["type"] == "text")` |
| `handle_tool_calls(content)` (private) | `_handle_tool_calls(self, content)` | `self._context.add_message("assistant", content)` (assistant message stored *before* dispatching — see Considerations), then for each `tool_use` block: `print(f"  tool call → {name}({args})")`, `result = self._registry.dispatch(name, args)`, `print(f"  tool result → {str(result)[:61]}")`, `self._context.add_message("tool_result", str(result), tool_use_id=use_id)` |
| `puts "  tool call → #{name}(#{args})"` (Ruby hash `#to_s` renders `{"path" => "README.md"}`) | `print(f"  tool call → {name}({args})")` | Python dict `repr`/`str` renders `{'path': 'README.md'}` (single quotes, no `=>`) — a cosmetic, language-native divergence, not a bug to paper over; note it in the README same as prior steps note their own cosmetic divergences |
| `result.to_s[0..60]` | `str(result)[:61]` | Ruby's inclusive range `[0..60]` is 61 characters; Python slice needs `[:61]` to match length exactly |
| `Config::PROMPTS_DIR = File.expand_path("../../../prompts", __dir__)` (buggy, resolves outside the step) | `PROMPTS_DIR = (Path(__file__).resolve().parent.parent / "prompts").resolve()` (unchanged from `04_api_client`) | fixed per the Decisions section — resolves to `python/05_agent_loop/prompts/`, not one level above the step root |
| `example.rb`'s `base_dir = File.expand_path("..", __dir__)` | `base_dir = Path(__file__).resolve().parent.parent` | the step root (parent of `examples/`), used to resolve tool paths so `read_file`/`list_directory` work regardless of the process's CWD |
| `read_file` tool: `File.read(File.expand_path(path, base_dir))` | `Path(base_dir, path).resolve().read_text()` | (`Path(base_dir, path)` treats `path` as relative to `base_dir` when it isn't already absolute, matching `File.expand_path(path, base_dir)`) |
| `list_directory` tool: `Dir.entries(File.expand_path(path, base_dir)).reject { starts_with "." }.join(", ")` | `", ".join(sorted(p.name for p in Path(base_dir, path).resolve().iterdir() if not p.name.startswith(".")))` | separator changes from `04_api_client`'s `"\n"` to `", "` per Ruby's own change this step; Python keeps its established `sorted(...)` (Ruby's `Dir.entries` order is filesystem-dependent/unspecified — this divergence was already noted as intentional in the `04_api_client` plan and carries forward unchanged) |
| `ctx.add_message(:user, "Read the README.md file and summarise what this MUD player assistant framework can do.")` | same string, `ctx.add_message("user", ...)` | |
| `agent = Boukensha::Agent.new(context: ctx, registry: registry, builder: builder, client: client, task_settings: player_settings)` | `agent = Agent(ctx, registry, builder, client, task_settings=player_settings)` | `max_iterations`/`max_output_tokens` left unset so `Agent` resolves them from `player_settings` |
| `puts "Max iterations: #{Tasks::Player.max_iterations(player_settings)}"` / `"Max output tokens: ..."` | same, `print(f"Max iterations: {Player.max_iterations(player_settings)}")` / `print(f"Max output tokens: {Player.max_output_tokens(player_settings)}")` | |
| `result = agent.run` ... `puts "=== FINAL RESPONSE ==="` ... `puts result` | same, `result = agent.run()`; `print(); print("=== FINAL RESPONSE ==="); print(result)` | |
| `puts "=== BOUKENSHA Step 5: Agent Loop ==="` | same | header text bumps to Step 5 |

## Config directory resolution (fixed — see Decisions)

Same as `04_api_client`: `BOUKENSHA_DIR` env var, else `~/.boukensha`,
resolved via `pathlib`. `PROMPTS_DIR` resolves to
`python/05_agent_loop/prompts/` using the same two-level-up expression every
prior Python step has used — Ruby's newly-introduced three-level-up typo is
**not** ported (see Decisions).

## Config schema (adds two optional keys, both already supported by `Tasks::Base`)

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
    max_iterations: 25        # optional, defaults to 25
    max_output_tokens: 1024   # optional, defaults to 1024
```

Both keys are optional — `Tasks::Base.max_iterations`/`.max_output_tokens`
fall back to `DEFAULT_MAX_ITERATIONS`/`DEFAULT_MAX_OUTPUT_TOKENS` (25 / 1024)
when absent, and `Agent` itself falls back again to its own
`MAX_ITERATIONS`/`None` if `task_settings` isn't supplied at all. The repo's
existing `.boukensha/settings.yaml` doesn't set either key, so the verified
output below was captured against the 25/1024 defaults.

## Verified Ruby output

Captured by running `./week1_baseline/bin/ruby/05_agent_loop` for real
against the repo's `.boukensha/` directory and a live Anthropic API key
(provider `anthropic`, model `claude-haiku-4-5`):

```
=== BOUKENSHA Step 5: Agent Loop ===

Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Max iterations: 25
Max output tokens: 1024

[iteration 1/25]
  tool call → read_file({"path" => "README.md"})
  tool result → # The Agent Loop

The Agent Loop is the heart of BOUKENSHA. E
[iteration 2/25]

=== FINAL RESPONSE ===
## Summary of BOUKENSHA MUD Player Assistant Framework

**BOUKENSHA** is an AI-powered MUD (Multi-User Dungeon) player assistant framework. Here's what it can do:

### Core Functionality
- **Agent Loop**: The framework runs an intelligent agent that sends requests to AI APIs, interprets responses, and dispatches tool calls in a continuous loop
- **Multi-Provider Support**: Works with 5 different AI providers:
  - Anthropic (Claude)
  - OpenAI
  - Google Gemini
  - Ollama (local)
  - Ollama Cloud (hosted)

### Key Features
1. **Normalized Response Handling**: Converts different API response formats from all 5 providers into a single unified format, simplifying the agent logic
2. **Tool Integration**: The agent can call tools (like `read_file` and `list_directory`) to interact with the game world, receiving results and using them to make decisions
3. **Task-Based Configuration**: Manages player tasks with configurable settings including provider/model selection, max iterations, output token limits, and custom system prompts
4. **Smart Loop Control**: Detects tool-use vs. done, handles multiple tool calls per turn, enforces iteration limits (default 25), manages message history correctly
5. **Flexible Backend Architecture**: Each provider gets its own backend implementation behind a common interface

### Use Case
Players issue goals to the agent, and it autonomously explores, fights, and interacts with the MUD game world by repeatedly reasoning, calling tools, and adapting to results.
```

This is what the Python port's output must match **field-for-field for the
labeled lines and loop structure** (header, Config/Provider/Model/Max
iterations/Max output tokens, `[iteration N/25]` markers, tool call/result
lines, `=== FINAL RESPONSE ===`). The model's actual tool choice and
generated text are inherently non-deterministic — a repeat run could take a
different number of iterations or produce different summary wording — so
the FINAL RESPONSE body is source-of-truth for *shape* (it read the README
via a tool call and produced a coherent summary), not for exact text,
matching the same caveat `04_api_client`'s plan documented for its raw
response body.

## Implementation steps

1. **Scaffold** `week1_baseline/python/05_agent_loop/` per the layout above;
   copy `requirements.txt` from `04_api_client` unchanged.
2. **`boukensha/tool.py`, `boukensha/message.py`, `boukensha/context.py`,
   `boukensha/config.py`, `boukensha/registry.py`,
   `boukensha/tasks/player.py`, `boukensha/backends/base.py`** — copy
   unchanged from `04_api_client`.
3. **`prompts/system.md`** — copy unchanged from `04_api_client`.
4. **`boukensha/errors.py`** — add `class LoopError(Exception): pass`
   alongside the existing three error classes (see Decisions — stays
   unused).
5. **`boukensha/tasks/base.py`** — copy from `04_api_client`, add
   `DEFAULT_MAX_ITERATIONS = 25`, `DEFAULT_MAX_OUTPUT_TOKENS = 1024` class
   attributes, `max_iterations(cls, settings)` /
   `max_output_tokens(cls, settings)` classmethods, and the private
   `integer_setting(settings, key, default)` helper per the mapping table.
6. **`boukensha/client.py`** — add `tools=None` param to `call`, thread it
   into `self.builder.to_api_payload(...)`; no other change to the
   retry/backoff logic.
7. **`boukensha/prompt_builder.py`** — add `tools=None` param to
   `to_api_payload`, thread into `self.backend.to_payload(...)`; add
   `parse_response(self, response)` delegating to the backend.
8. **`boukensha/backends/anthropic.py`** — add `tools=None` param to
   `to_payload` (`tools if tools is not None else self.to_tools(...)`), add
   `parse_response` per the mapping table.
9. **`boukensha/backends/gemini.py`** — same `tools` param change; add
   `parse_response`; add private `_assistant_parts`; update the
   `:assistant` branch of `to_messages` to call it.
10. **`boukensha/backends/ollama.py`** and **`ollama_cloud.py`** — same
    `tools` param change in each; add `parse_response` (identical body in
    both, matching Ruby's duplication) and private `_assistant_message` to
    each; add an `elif msg.role == "assistant":` branch to each's
    `to_messages`.
11. **`boukensha/backends/openai.py`** — add `import json` at module top;
    same `tools` param change; add `parse_response` (using `json.loads` for
    tool-call arguments) and private `_assistant_message` (using
    `json.dumps` for the reverse direction); add the `:assistant` branch to
    `to_messages`.
12. **`boukensha/agent.py`** — new `Agent` class per the mapping table:
    `MAX_ITERATIONS = 25`, `WRAP_UP_OUTPUT_TOKENS = 400`,
    `WRAP_UP_DIRECTIVE` string; `__init__` resolving `_max_iterations`/
    `_max_output_tokens` via the private resolver methods; `run`; private
    `_resolve_max_iterations`, `_resolve_max_output_tokens`,
    `_iteration_limit_reached`, `_call_opts`, `_wrap_up`,
    `_fallback_message`, `_extract_text`, `_handle_tool_calls`. Import
    `ApiError` from `.errors` for the `_wrap_up` `except` clause.
13. **`boukensha/__init__.py`** — add `Agent` and `LoopError` to the
    existing re-exports from `04_api_client`.
14. **`examples/example.py`** — port `example.rb` per the mapping table:
    compute `base_dir` as the step root; `read_file`/`list_directory` tools
    resolve paths against it (comma-joined directory listing, sorted per
    the `04_api_client`-established divergence); single user message about
    reading the README; same 5-provider branch as `04_api_client`'s example
    to construct the backend; build `PromptBuilder`, `Client`, and `Agent`
    (passing `task_settings=player_settings`); print the labeled header
    lines (Config, Provider, Model, Max iterations, Max output tokens); call
    `agent.run()`; print the `=== FINAL RESPONSE ===` block.
15. **`week1_baseline/bin/python/05_agent_loop`** — new bash script, same
    template as every prior step's entry script:
    ```bash
    #!/usr/bin/env bash

    cd "$(dirname "$0")/../../python/05_agent_loop"
    source .venv/bin/activate
    python examples/example.py
    ```
    (`chmod +x`).
16. **`README.md`** in `python/05_agent_loop/` — same shape as the Ruby
    README (intro, How It Works diagram, `Agent` method table, "Every
    Backend Speaks the Same Normalized Shape" section incl. the
    id-reuse-for-providers-without-call-ids note, Task Configuration incl.
    the two new optional settings, "What the Loop Looks Like" using this
    port's own live run, Considerations, Run Example) — with New/Updated
    Files tables reflecting the *actual* diff-verified changes (per the
    stale-README Decision above, not copied from Ruby's tables), and a
    short note on the two Python-specific divergences: the fixed
    `PROMPTS_DIR` (see Decisions) and the cosmetic dict-repr difference in
    the `tool call → name(args)` log line (Python `{'path': ...}` vs Ruby's
    `{"path" => ...}`).
17. **Verify**: run `./week1_baseline/bin/python/05_agent_loop` for real and
    confirm the printed structure matches "Verified Ruby output" above —
    labeled header lines, `[iteration N/25]` markers, tool call/result log
    lines, `=== FINAL RESPONSE ===` — not exact text, per the Decisions/
    Verified-output caveats. Also smoke-test the wind-down path directly
    (e.g. construct an `Agent` with `max_iterations=1` against a task that
    triggers a tool call, confirm it takes exactly one wrap-up call with
    `tools=[]` and returns non-empty text) since the happy path alone may
    not reach it.

## Out of scope for this step

- No MUD connection / no actual `look`/`move` gameplay tools — this step's
  example still uses the filesystem tools (`read_file`, `list_directory`)
  introduced in `04_api_client`, per Ruby's own `example.rb`.
- No cost/usage logging beyond what `Base#estimate_cost` (from
  `03_prompt_builder`) already exposes — `Agent` doesn't call it.
- No new config keys beyond `max_iterations`/`max_output_tokens`, both
  optional with defaults.
- No `pyproject.toml`/packaging, no CLI entry-point registration, no test
  suite, no third-party HTTP dependency — per precedent from every prior
  step.
- No fixes to rough edges already carried over from `00_config`/
  `01_struct_skeleton`/`02_the_registry`/`03_prompt_builder`/`04_api_client`
  (`.yml` extension question, missing-settings-file handling,
  `Context`/`Registry`'s dual ownership of tools, Ollama's hardcoded local
  address, `Client` not being fully stateless).
- `LoopError` stays defined-but-unreachable, matching Ruby — no iteration
  ceiling is ever enforced via an exception; `wrap_up` is the only ceiling
  mechanism, in both languages (see Decisions).
</content>
