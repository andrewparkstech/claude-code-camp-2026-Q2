# The Agent Loop (Python port)

Python port of `week1_baseline/ruby/05_agent_loop`. Same behavior, same
output shape (aside from the display divergences noted below). This is the
heart of BOUKENSHA — everything built before this (structs, registry, prompt
builder, client) was setup. `Agent` is where the model's tool calls actually
get dispatched, results get replayed into the conversation, and the turn
ends either because the model says it's done or because an iteration
ceiling forces a wind-down.

## Setup

```bash
cd week1_baseline/python/05_agent_loop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## New Files

| File | Description |
|---|---|
| `boukensha/agent.py` | The agent loop — sends requests, dispatches tools, and knows when to stop |

## Updated Files

| File | Change |
|---|---|
| `boukensha/errors.py` | Added `LoopError` (defined for parity with Ruby; unused in both languages — see Considerations) |
| `boukensha/tasks/base.py` | Added `max_iterations`/`max_output_tokens` classmethods, each backed by a new integer-coercing settings helper |
| `boukensha/client.py` | `call` gained a `tools=` param, threaded into the payload build |
| `boukensha/prompt_builder.py` | Added `parse_response`, delegating to the backend; `to_api_payload` gained a `tools=` param |
| `boukensha/backends/*.py` | Every backend gained `parse_response`, normalizing its response into a common `{stop_reason, content}` shape, and a `tools=` param on `to_payload`. `ollama.py`, `ollama_cloud.py`, and `openai.py` also gained a private `_assistant_message` helper (the inverse of `parse_response`) and an `assistant`-role branch in `to_messages`; `gemini.py` gained the equivalent `_assistant_parts` |

Everything else (`config.py`, `tool.py`, `message.py`, `context.py`,
`registry.py`, `tasks/player.py`, `backends/base.py`) is an unchanged copy
from `04_api_client` — confirmed by diffing the Ruby sources, this step
doesn't touch them.

*(Ruby's own README for this step lists `backends/base.rb`, `tasks/base.rb`,
`tasks/player.rb`, `backends/openai.rb`, `backends/gemini.rb`,
`backends/ollama_cloud.rb`, and `prompts/system.md` as "New Files", and
credits `context.rb`/`config.rb` with changes ("carries the active task
object", "reads tasks.player instead of top-level settings") — none of that
is accurate for this diff. That functionality already existed as of
`00_config` through `04_api_client`. The tables above reflect what actually
changed.)*

## How It Works

```
send messages to API
        ↓
stop_reason == "tool_use"?
    yes → extract tool calls
        → dispatch each tool via Registry
        → inject results as tool_result messages
        → go back to top
    no  → return final text response
```

## Agent

| Method | Description |
|---|---|
| `run()` | Starts the loop and returns the final text response when the agent is done |

## Every Backend Speaks the Same Normalized Shape

Five providers means five different response formats — Anthropic nests tool
calls inside `content`, Ollama puts them in `message.tool_calls`, OpenAI
nests them under `choices[0].message.tool_calls`, and Gemini calls them
`functionCall` parts. Rather than teach the loop about each of these, every
backend implements `parse_response`, converting its raw response into one
common shape:

```python
{
    "stop_reason": "tool_use" | "end_turn",
    "content": [
        {"type": "text", "text": "..."},
        {"type": "tool_use", "id": "...", "name": "...", "input": {...}},
    ],
}
```

`Agent` only ever sees this shape — it calls
`self._builder.parse_response(response)`, which delegates to the backend,
and never inspects a raw provider response.

The conversion also runs in reverse. When the conversation history is
replayed on the next request, Ollama, Ollama Cloud, OpenAI, and Gemini each
rebuild a provider-specific assistant message from the normalized `content`
blocks via a private `_assistant_message` (or `_assistant_parts`) method —
the inverse of `parse_response`. Anthropic's `content` array doubles as
both the normalized shape and the wire format, so it needs no extra
conversion.

**Tool call IDs aren't universal.** Anthropic and OpenAI assign every tool
call a unique `id`, echoed back in the `tool_result`. Ollama, Ollama Cloud,
and Gemini don't assign call ids at all — those backends reuse the tool's
`name` as its `id` and match the `tool_result` back to the call by name.

## Task Configuration

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
    max_iterations: 25
    max_output_tokens: 1024
```

When `prompt_override.system` is true, Boukensha reads
`.boukensha/prompts/player/system.md`. Otherwise it falls back to this
step's shipped `prompts/system.md`. `max_iterations` controls model
round-trips per turn before wind-down, and `max_output_tokens` is passed to
each model reply. Both keys are optional — `Tasks::Base.max_iterations`/
`.max_output_tokens` fall back to 25/1024 when absent, and `Agent` falls
back again to its own default if no `task_settings` are supplied at all.

## What the Loop Looks Like

Running the example produces output like this (captured from a live run
against this repo's `.boukensha/`, provider `anthropic`, model
`claude-haiku-4-5`):

```
=== BOUKENSHA Step 5: Agent Loop ===

Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Max iterations: 25
Max output tokens: 1024

[iteration 1/25]
  tool call → read_file({'path': 'README.md'})
  tool result → # The Agent Loop (Python port)

Python port of `week1_
[iteration 2/25]

=== FINAL RESPONSE ===
Here are the files in the current directory: README.md, examples, boukensha, requirements.txt.
The BOUKENSHA framework lets you build an AI agent that plays a MUD...
```

The model's actual tool choice and generated text are non-deterministic —
the labeled lines, `[iteration N/max]` markers, and overall loop shape are
what should match run to run, not the exact summary text.

## Considerations

**The assistant message must be stored before the tool result.** The
Anthropic API requires the assistant's tool_use block to appear in the
message history before its corresponding tool_result. `_handle_tool_calls`
adds the assistant message first — get the order wrong and the API rejects
the request.

**The model can call multiple tools in one turn.** The loop handles this by
iterating over all `tool_use` blocks in a single response before making the
next API call.

**`MAX_ITERATIONS` is a turn ceiling.** A poorly prompted agent can loop
forever if the model keeps calling tools. BOUKENSHA stops starting new work
after 25 iterations by default and makes one short wrap-up call with tools
disabled. This keeps the turn bounded while still returning a useful final
response.

**The agent has no way to stop itself.** The model signals it is done via
`stop_reason: "end_turn"`. BOUKENSHA watches for that signal and exits the
loop. The agent never decides unilaterally to stop.

**`LoopError` is defined but never raised.** Ruby's `errors.rb` adds it
("for runaway agents") but nothing in `agent.rb` actually raises it — the
iteration ceiling is enforced entirely through the wind-down call, never an
exception. The Python port matches this: the class exists for parity, but
nothing in `agent.py` raises it.

## Run Example

```bash
./week1_baseline/bin/python/05_agent_loop
```

Field-for-field structure (labeled header lines, iteration markers, tool
call/result lines, `=== FINAL RESPONSE ===`) matches the Ruby run captured
in [docs/plans/python_port/05_agent_loop.md](../../../docs/plans/python_port/05_agent_loop.md).

## Ruby → Python idiom differences

- **`PROMPTS_DIR` fix.** Ruby's `config.rb` in this step picked up an extra
  `../` (`File.expand_path("../../../prompts", __dir__)`), making
  `PROMPTS_DIR` resolve one directory above the step root — a path that
  doesn't exist. This repo's `.boukensha/settings.yaml` masks it (
  `prompt_override.system: true` points at a user prompt file that exists),
  but if that override were off, Ruby's default system prompt would
  silently come back `nil`. The Python port keeps the same two-level-up
  expression every prior step has used, resolving correctly to
  `python/05_agent_loop/prompts/`.
- **Tool call log formatting.** Python's dict `repr` renders
  `{'path': 'README.md'}` (single quotes, no `=>`) where Ruby's Hash
  `#to_s` renders `{"path" => "README.md"}` — a cosmetic, language-native
  difference in the `tool call → name(args)` log line, not a behavior
  divergence.
- `Dir.entries` (Ruby, filesystem order, unspecified) stays
  `sorted(...)` in `examples/example.py`'s `list_directory` tool, per the
  divergence already established in `04_api_client`. The join separator
  changes from `04_api_client`'s `"\n"` to `", "`, matching Ruby's own
  change in this step.
- Ollama's and Ollama Cloud's `parse_response`/`_assistant_message` bodies
  are identical between the two backend files, matching Ruby's own
  duplication rather than factoring out a shared helper — not a decision
  made by this port, just carried straight across.

## Out of scope

- No MUD connection / no actual `look`/`move` gameplay tools — the example
  still uses the filesystem tools (`read_file`, `list_directory`)
  introduced in `04_api_client`, matching Ruby's own `example.rb`.
- No cost/usage logging beyond what `Base.estimate_cost` (from
  `03_prompt_builder`) already exposes — `Agent` doesn't call it.
- `Context`/`Registry`'s dual ownership of tools, flagged in the
  `02_the_registry` port's README, is still unresolved here — carried
  forward unchanged.
- Ollama's backend still hardcodes `http://localhost:11434` rather than
  reading an env var, and `Client` still holds `builder` as instance state
  rather than being fully stateless — both acknowledged as known trade-offs
  in Ruby's own README, carried forward unchanged to match.
