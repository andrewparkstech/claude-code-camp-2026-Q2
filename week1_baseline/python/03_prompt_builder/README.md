# The Prompt Builder (Python port)

Python port of `week1_baseline/ruby/03_prompt_builder`. Same behavior, same
output shape (aside from the display divergences noted below) — builds on
the `Tool`/`Message`/`Context`/`Registry` code ported in
`python/02_the_registry`.

Because LLM access, cost and quality are constantly changing, we want to be
able to switch between multiple LLMs that will drive the agent loop.

There are several SDKs that provide access to many LLMs but in practice we
only really need to focus on top-tier models:
- anthropic family
- openai family
- gemini family
- ollama cloud eg. kimi, minimax, llama

The Prompt Builder serializes `Context` for the exact format each API
expects. `PromptBuilder` delegates to whichever backend you pass in.

`PromptBuilder` does not call the API, we are simply preparing the format
for API calls.

Configuration is task-based here, carried forward from the registry step.
The `player` task owns its provider, model, and prompt override settings,
and the context records the task that the prompt is being built for.

## Setup

```bash
cd week1_baseline/python/03_prompt_builder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## New Files

| File | Description |
|---|---|
| `boukensha/prompt_builder.py` | Delegates serialization to the active backend |
| `prompts/system.md` | Default system prompt used when a task does not override it |
| `boukensha/backends/base.py` | Shared backend contract for model validation and model metadata |
| `boukensha/backends/anthropic.py` | Serializes context into the Anthropic API format |
| `boukensha/backends/ollama.py` | Serializes context into the Ollama API format |
| `boukensha/backends/ollama_cloud.py` | Serializes context into the Ollama Cloud API format |
| `boukensha/backends/openai.py` | Serializes context into the OpenAI Chat Completions format |
| `boukensha/backends/gemini.py` | Serializes context into the Gemini `generateContent` format |

## How It Works

```
Context (Python objects)
        ↓
PromptBuilder
        ↓
Backend (Anthropic, OpenAI, Gemini, or Ollama)
        ↓
API Payload (plain dicts and lists)
        ↓
POST to API
```

## PromptBuilder

| Method | Description |
|---|---|
| `to_messages()` | Delegates message serialization to the backend |
| `to_tools()` | Delegates tool serialization to the backend |
| `to_api_payload(max_output_tokens=1024)` | Assembles the complete payload ready to POST |
| `headers` | Returns the correct headers for the backend |
| `url` | Returns the correct endpoint URL for the backend |

## Backends

Each API has its own conventions for how data is expected. Anthropic and
Gemini are the most alike (system prompt as a top-level field), while
OpenAI and Ollama share the same `function`-wrapped tool schema.

Backends also own their supported model table. A backend refuses to
initialize with an unknown model, so `settings.yaml` cannot silently select
an unsupported or misspelled model. Each model entry carries:

| Key | Meaning |
|---|---|
| `context_window` | The model's known token context window |
| `cost_per_million.input` | USD input token price per million tokens, when known |
| `cost_per_million.output` | USD output token price per million tokens, when known |
| `usage_unit` | `"tokens"`, `"local_compute"`, or `"ollama_cloud_usage"` |
| `usage_level` | Ollama Cloud usage tier, when applicable |

Backend instances expose `context_window`, `input_token_cost_per_million`,
`output_token_cost_per_million`, `usage_unit`, `usage_level`, and
`estimate_cost(input_tokens, output_tokens)`. For local Ollama models, token
API cost is `0.0`. For Ollama Cloud, public pricing is plan/usage based
rather than token based, so `estimate_cost` returns `None`.

The prices in this step are static tutorial data, current as of June 16,
2026, and should be reviewed whenever the selected model set changes.

### Anthropic

Talks to `https://api.anthropic.com/v1/messages`. Requires an
`ANTHROPIC_API_KEY`. Supported models are listed in `Anthropic.MODELS`.

### Ollama

Talks to `http://localhost:11434/api/chat`. Requires `ollama serve` running
locally. No API key needed. Supported models are listed in `Ollama.MODELS`.

### OllamaCloud

Talks to `https://ollama.com/api/chat`. Requires an `OLLAMA_API_KEY`.
Supported models are listed in `OllamaCloud.MODELS`.

### OpenAI

Talks to `https://api.openai.com/v1/chat/completions`. Requires an
`OPENAI_API_KEY`. Supported models are listed in `OpenAI.MODELS`.

### Gemini

Talks to `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`.
Requires a `GEMINI_API_KEY`. Supported models are listed in `Gemini.MODELS`.

### System Prompt

Anthropic and Gemini send the system prompt as a top-level field, separate
from the messages array. Ollama and OpenAI put it inside the messages array
as a `role: system` message.

```json
// Anthropic
{ "system": "You are a MUD player assistant.", "messages": [ ... ] }

// Gemini
{ "systemInstruction": { "parts": [{ "text": "You are a MUD player assistant." }] }, "contents": [ ... ] }

// Ollama / OpenAI
{ "messages": [ { "role": "system", "content": "You are a MUD player assistant." }, ... ] }
```

### Tool Results

Anthropic wraps tool results in a user message. Ollama and OpenAI use their
own `role: tool` message type (with slightly different identifier fields).
Gemini wraps results in a `functionResponse` part on a `user` message.

```json
// Anthropic
{ "role": "user", "content": [{ "type": "tool_result", "tool_use_id": "toolu_01X", "content": "A damp stone corridor stretches north. Torches flicker on the walls." }] }

// Ollama
{ "role": "tool", "tool_name": "look", "content": "A damp stone corridor stretches north. Torches flicker on the walls." }

// OpenAI
{ "role": "tool", "tool_call_id": "toolu_01X", "content": "A damp stone corridor stretches north. Torches flicker on the walls." }

// Gemini
{ "role": "user", "parts": [{ "functionResponse": { "name": "toolu_01X", "response": { "content": "A damp stone corridor stretches north. Torches flicker on the walls." } } }] }
```

### Tool Definitions

Anthropic uses `input_schema`. Ollama and OpenAI wrap everything in a
`function` envelope with `parameters`. Gemini wraps tools in a
`functionDeclarations` array.

```json
// Anthropic
{ "name": "move", "description": "Move the player in a direction (north, south, east, west, up, down)", "input_schema": { "type": "object", "properties": { "direction": { "type": "string", "description": "The direction to move" } }, "required": ["direction"] } }

// Ollama / OpenAI
{ "type": "function", "function": { "name": "move", "description": "Move the player in a direction (north, south, east, west, up, down)", "parameters": { "type": "object", "properties": { "direction": { "type": "string", "description": "The direction to move" } }, "required": ["direction"] } } }

// Gemini
{ "functionDeclarations": [ { "name": "move", "description": "Move the player in a direction (north, south, east, west, up, down)", "parameters": { "type": "object", "properties": { "direction": { "type": "string", "description": "The direction to move" } }, "required": ["direction"] } } ] }
```

### Message Roles

Anthropic, Ollama, and OpenAI all use `assistant` for the model's turn.
Gemini calls it `model`.

```json
// Anthropic / Ollama / OpenAI
{ "role": "assistant", "content": "Let me take a look around first." }

// Gemini
{ "role": "model", "parts": [{ "text": "Let me take a look around first." }] }
```

## Considerations

**The conversation is stateless.** The model has no memory between turns.
Every API call includes the entire history from the beginning. BOUKENSHA is
responsible for carrying that state.

**Tool results are user messages on Anthropic.** This feels
counterintuitive — the result came from BOUKENSHA, not the human — but it
reflects how the Anthropic API models the conversation. Ollama, OpenAI, and
Gemini all handle this with dedicated message/part types instead.

**The agent only sees schemas.** The `description` field on each tool is the
only thing the agent uses to decide which tool to call. The actual block
never leaves BOUKENSHA.

## Run Example

```bash
./week1_baseline/bin/python/03_prompt_builder
```

Expected output (values from your `.boukensha/`; this run used provider
`anthropic`, model `claude-haiku-4-5`):

```
=== BOUKENSHA Step 3: Prompt Builder ===

Config: #<Boukensha::Config dir=/home/andrew/Sites/Claude-Code-Camp/.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
{
  "model": "claude-haiku-4-5",
  "system": "You are a MUD Journey Player Agent. You are playing the MUD on behalf of the player, The player will issue you goals to complete. Use the tools available to you to help the player explore, fight, and interact with the world.",
  "max_tokens": 1024,
  "tools": [
    {
      "name": "look",
      "description": "Look around the current room for details",
      "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
      }
    },
    {
      "name": "move",
      "description": "Move the player in a direction (north, south, east, west, up, down)",
      "input_schema": {
        "type": "object",
        "properties": {
          "direction": {
            "type": "string",
            "description": "The direction to move"
          }
        },
        "required": [
          "direction"
        ]
      }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "I just arrived in the dungeon. What's around me, and can you move north?"
    },
    {
      "role": "assistant",
      "content": "Let me take a look around first."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_01X",
          "content": "A damp stone corridor stretches north. Torches flicker on the walls."
        }
      ]
    }
  ]
}
```

This was captured by running `./week1_baseline/bin/ruby/03_prompt_builder`
and `./week1_baseline/bin/python/03_prompt_builder` side by side — the two
outputs are byte-identical apart from your machine's config path and the
`Boukensha::Config` naming choice noted below. The active provider/model
come from your `.boukensha/settings.yaml`; only the four other backends
(`Gemini`, `Ollama`, `OllamaCloud`, `OpenAI`) are ported but not exercised
unless you configure the `player` task to use one of them.

## Ruby → Python idiom differences

- **`model_info` naming split.** Ruby's `Backends::Base` has a class method
  `self.model_info(model)` (table lookup by name) and an instance method
  `model_info` (no-arg accessor for the configured model's data) — legal in
  Ruby because class methods and instance methods live in separate
  namespaces. Python has one namespace per class, so they'd collide. This
  port renames the classmethod to `model_info_for(model)` and keeps the
  instance side as a plain attribute `self.model_info` (set once in
  `_configure_model`, not wrapped in an accessor method, since Ruby's
  instance `model_info` was itself just `@model_info` with no logic).
- **Ruby symbols become plain strings.** `usage_unit: :tokens` /
  `:local_compute` / `:ollama_cloud_usage` and `usage_level: :medium` /
  `:high` become the strings `"tokens"`, `"local_compute"`,
  `"ollama_cloud_usage"`, `"medium"`, `"high"` — same treatment already
  given to `Message#role` symbols in `01_struct_skeleton`.
- **`0.0` vs `nil`/`None` in `estimate_cost`.** Ruby's `unless a && b` on
  `0.0` costs (Ollama's local models) is truthy in Ruby — only `nil`/`false`
  are falsy there — so `estimate_cost` returns a real `0.0`, not `nil`.
  Python's `0.0` is falsy, so a naive `if not a or not b` port would
  incorrectly return `None` for Ollama. This port checks `is None`
  explicitly instead of truthiness, matching Ruby's actual behavior
  (verified by running both languages' `estimate_cost` on an Ollama model).
- **No bang methods.** `validate_model!` has no Python equivalent naming
  convention; it's `validate_model` here, still raising
  `UnsupportedModelError` on a miss.
- `Tool#parameters.keys` prints as `[:direction]` in Ruby (symbol keys) vs
  `['direction']` in Python (string keys) — same display divergence already
  noted in the `01_struct_skeleton` port.
- `Config`'s `__str__` keeps the `Boukensha::Config` string byte-identical
  to Ruby, same choice made in every prior port in this series.

## Out of scope

- No networking / no actual API calls to any of the 5 providers — this step
  only builds payloads, matching the Ruby version's explicit scope.
- `Context`/`Registry`'s dual ownership of tools, flagged in the
  `02_the_registry` port's README, is still unresolved here — carried
  forward unchanged, to be corrected in a later step.
