# Python Port Plan · 03_prompt_builder

Port `week1_baseline/ruby/03_prompt_builder` to
`week1_baseline/python/03_prompt_builder`, preserving behavior and output
shape exactly (module-name-in-string differences aside — see the mapping
table). This step adds `PromptBuilder`, five backend classes
(`Anthropic`, `Gemini`, `Ollama`, `OllamaCloud`, `OpenAI`), and reintroduces
`Config::PROMPTS_DIR` + a shipped `prompts/system.md` on top of the
`Tool`/`Message`/`Context`/`Registry` structures already ported in
[01_struct_skeleton](01_struct_skeleton) and [02_the_registry](02_the_registry).
It's a straight port of the current step only: no networking (the Ruby
README is explicit that `PromptBuilder` never calls an API, it only builds
the payload), no new config keys beyond what Ruby's `03_prompt_builder`
itself adds, no fixes to known rough edges already carried over from earlier
steps.

## Decisions (confirmed with user)

- **`model_info` naming collision**: Ruby's `Backends::Base` has a class
  method `self.model_info(model)` (table lookup by name) and an instance
  method `model_info` (no-arg accessor for the configured model's data) —
  legal in Ruby because class methods and instance methods live in separate
  namespaces. Python has one namespace per class, so they collide. Resolved
  by renaming the classmethod to `model_info_for(model)` and keeping the
  instance side as a plain attribute `self.model_info` (set once in
  `_configure_model`, not wrapped in an accessor method — idiomatic Python,
  since Ruby's instance `model_info` was itself just `@model_info` with no
  logic).
- **Symbol fields (`usage_unit`, `usage_level`) become plain strings**:
  `:tokens` → `"tokens"`, `:local_compute` → `"local_compute"`,
  `:ollama_cloud_usage` → `"ollama_cloud_usage"`, `:medium` → `"medium"`,
  `:high` → `"high"`. Same treatment already given to `Message#role`
  symbols (`:user`/`:assistant` → `"user"`/`"assistant"`) in
  `01_struct_skeleton` — no new Enum pattern introduced into the port series
  for this step.
- Everything else follows the precedent already set by `00_config`,
  `01_struct_skeleton`, `02_the_registry`: self-contained per-step directory
  (duplicate `config.py`/`tasks/`/`context.py`/etc. rather than import across
  step directories), plain `venv` + `requirements.txt` (`PyYAML`,
  `python-dotenv` — no HTTP client added, since this step never makes a
  network call), no test suite (the Ruby version has none), entry point at
  `week1_baseline/bin/python/03_prompt_builder`.

## Target directory layout

```
week1_baseline/python/03_prompt_builder/
  requirements.txt          # PyYAML, python-dotenv (unchanged from 02_the_registry)
  README.md                 # same shape as the Ruby README, Python-specific run example
  prompts/
    system.md                # shipped default system prompt (byte-identical to Ruby's)
  boukensha/
    __init__.py              # re-exports Config, Context, Message, Player, Tool, Registry,
                              # UnknownToolError, UnsupportedModelError, PromptBuilder,
                              # and the five backend classes
    config.py                # ported from 02_the_registry, PROMPTS_DIR constant re-added
    tool.py                  # unchanged port from 02_the_registry
    message.py                # unchanged port from 02_the_registry
    context.py                # unchanged port from 02_the_registry
    errors.py                # adds UnsupportedModelError alongside UnknownToolError
    registry.py               # unchanged port from 02_the_registry
    prompt_builder.py         # new — PromptBuilder class
    tasks/
      __init__.py
      base.py                # unchanged port from 02_the_registry
      player.py               # unchanged port from 02_the_registry
    backends/
      __init__.py
      base.py                # new — Backends.Base shared contract
      anthropic.py            # new
      gemini.py               # new
      ollama.py               # new
      ollama_cloud.py         # new
      openai.py               # new
  examples/
    example.py                 # smoke test, same shape as example.rb

week1_baseline/bin/python/03_prompt_builder   # new — parallel to bin/python/02_the_registry
```

`tool.py`, `message.py`, `context.py`, `registry.py`, `tasks/base.py`,
`tasks/player.py` are byte-identical in Ruby between `02_the_registry` and
`03_prompt_builder` (confirmed via `diff` — the only Ruby-side changes in
this step outside the new `prompt_builder.rb`/`backends/` files are: (1)
`config.rb` re-adds the `PROMPTS_DIR` constant it had in `00_config` but lost
in `01_struct_skeleton`/`02_the_registry`, (2) `context.rb` drops the stray
unfinished comment that `02_the_registry`'s had — already not carried into
`context.py` per the `02_the_registry` plan, so no change needed there, (3)
`errors.rb` adds `UnsupportedModelError`). Copy the five unchanged files from
`02_the_registry`'s Python port unchanged.

## Ruby → Python mapping

| Ruby | Python | Notes |
|---|---|---|
| `Boukensha::UnsupportedModelError < StandardError` | `class UnsupportedModelError(Exception)` | same StandardError→Exception treatment as `UnknownToolError` in `02_the_registry` — no custom hierarchy |
| `PROMPTS_DIR = File.expand_path("../../prompts", __dir__)` | `PROMPTS_DIR = (Path(__file__).resolve().parent.parent / "prompts").resolve()` | same expression already used in `00_config`'s Python port before it was dropped in `01_struct_skeleton`; reinstated here to match Ruby re-adding it |
| `PromptBuilder#initialize(context, backend)` | `PromptBuilder.__init__(self, context, backend)` | `self.context`, `self.backend`, same as Ruby ivars |
| `to_messages` → `@backend.to_messages(@context.messages)` | `to_messages(self)` → `self.backend.to_messages(self.context.messages)` | |
| `to_tools` → `@backend.to_tools(@context.tools)` | `to_tools(self)` → `self.backend.to_tools(self.context.tools)` | |
| `to_api_payload(max_output_tokens: 1024)` | `to_api_payload(self, max_output_tokens=1024)` | delegates to `self.backend.to_payload(self.context, max_output_tokens=max_output_tokens)` |
| `headers` / `url` | `headers(self)` / `url(self)` | plain delegation to backend |
| `Backends::Base.models` (`const_get(:MODELS)`, `NotImplementedError` if missing) | `Base.models(cls)` classmethod → `cls.MODELS` if defined on the class, else `raise NotImplementedError(f"{cls.__name__} must define MODELS")` | Python has no `const_get`/`rescue NameError` idiom — use `getattr(cls, "MODELS", None)` and raise explicitly when `None` |
| `Backends::Base.model_info(model)` (class method) | `Base.model_info_for(cls, model)` classmethod | renamed per the Decisions section to avoid colliding with the instance-level attribute |
| `Backends::Base.validate_model!(model)` | `Base.validate_model(cls, model)` classmethod | Ruby's bang convention has no Python equivalent; raises `UnsupportedModelError` with the same message format, `sorted(cls.models().keys())` joined with `", "` |
| `model_info` (instance method, `@model_info`) | `self.model_info` plain attribute | set inside `_configure_model`; no wrapper method (see Decisions) |
| `context_window` / `input_token_cost_per_million` / `output_token_cost_per_million` / `usage_unit` / `usage_level` (instance methods reading `model_info`) | same names as Python `@property` methods reading `self.model_info` | `usage_level` uses `.get("usage_level")` (may be absent/`None`), matching Ruby's `model_info[:usage_level]` (no `.fetch`) |
| `estimate_cost(input_tokens:, output_tokens:)` | `estimate_cost(self, input_tokens, output_tokens)` | returns `None` if either per-million cost is `None`/falsy, else same formula `/ 1_000_000.0` |
| `configure_model(model)` (private) | `_configure_model(self, model)` | sets `self.model = self.validate_model(model)` then `self.model_info = self.model_info_for(self.model)`, called from each subclass `__init__` |
| Each backend's `MODELS` Hash (frozen, symbol keys for nested fields) | `MODELS: dict[str, dict]` class attribute, string keys throughout | e.g. `{"claude-haiku-4-5": {"context_window": 200_000, "cost_per_million": {"input": 1.0, "output": 5.0}, "usage_unit": "tokens"}}` — same numeric values, same model names, verbatim across all 5 backends |
| `tool.parameters.keys.map(&:to_s)` (building `required`) | `list(tool.parameters.keys())` | Python dict keys are already strings — no `.map(&:to_s)` needed, same simplification precedent as `02_the_registry`'s `dispatch` |
| `msg.role` symbol comparisons (`when :tool_result`, `when :assistant`) | `if msg.role == "tool_result"` / `elif msg.role == "assistant"` | plain string comparison, matching the symbol→string mapping decision |
| Anthropic/Gemini: `system` as top-level payload field | same, `context.system` passed directly | |
| Ollama/OllamaCloud/OpenAI: `to_messages(system, messages)` (two args, prepends a `role: system` message) | `to_messages(self, system, messages)` | note this backend group's `to_messages` signature differs from Anthropic/Gemini's one-arg `to_messages(messages)` **in Ruby itself** — `PromptBuilder#to_messages` (`@backend.to_messages(@context.messages)`) only ever calls the one-arg form; the two-arg form is only reached via each backend's own `to_payload`, never through `PromptBuilder#to_messages` directly. Port this exact asymmetry as-is, it's not a bug to fix in this step. |
| `OllamaCloud`'s `advertised_context_window` key on `minimax-m3:cloud` | same key, present only on that one entry | not read by any `Base` method (Ruby doesn't expose it via a reader either) — carried into the Python dict verbatim as inert data, matching Ruby |
| `Ollama.new(host: "http://localhost:11434", model:)` | `Ollama.__init__(self, model, host="http://localhost:11434")` | only Ollama backend takes no `api_key` |
| `JSON.pretty_generate(builder.to_api_payload)` | `json.dumps(builder.to_api_payload(), indent=2)` | Ruby's `pretty_generate` (2-space indent, `": "` object separator, no trailing whitespace) matches Python's `json.dumps(..., indent=2)` byte-for-byte; verified against the captured Ruby output below |
| `lib/boukensha.rb` requires | `boukensha/__init__.py` | adds `PromptBuilder`, `UnsupportedModelError`, and the five backend classes to the re-exports already present from `02_the_registry` |
| Provider dispatch in `example.rb` (`case provider when "anthropic" ... end`) | `if provider == "anthropic": ... elif ...` chain in `example.py` | same provider strings, same env var names (`ANTHROPIC_API_KEY`, `OLLAMA_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`), same `ArgumentError`-equivalent (`ValueError`) on an unrecognized provider |

## Config directory resolution (mostly unchanged, PROMPTS_DIR reinstated)

`BOUKENSHA_DIR` env var, else `~/.boukensha`, resolved via `pathlib` — same
as prior steps. New in this step: `Config.PROMPTS_DIR` is reinstated as a
module-level constant pointing at `python/03_prompt_builder/prompts/`
(mirroring Ruby's `File.expand_path("../../prompts", __dir__)` relative to
`lib/boukensha/config.rb`). This constant was present in `00_config`, absent
in `01_struct_skeleton`/`02_the_registry` (both Ruby and Python, tracked in
the `01_struct_skeleton` plan's mapping table), and Ruby's
`03_prompt_builder/config.rb` re-adds it — this port follows suit.

## Config schema (unchanged)

No new `settings.yaml` keys. Same shape as `00_config`/`01_struct_skeleton`/
`02_the_registry`. The repo's existing `.boukensha/settings.yaml` already has
`tasks.player.provider: anthropic` and `tasks.player.model:
claude-haiku-4-5`, which is what the verified output below was captured
against.

## Verified Ruby output (source of truth for this port)

Captured by running `./week1_baseline/bin/ruby/03_prompt_builder` against
the repo's existing `.boukensha/` directory (provider `anthropic`, model
`claude-haiku-4-5`, with a `prompt_override.system: true` task setting and a
matching `.boukensha/prompts/player/system.md` override file already present
on disk):

```
=== BOUKENSHA Step 3: Prompt Builder ===

Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>
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

This is what the Python port's output must match field-for-field (adjusted
only for the `Boukensha::Config` naming divergence already established in
prior steps' READMEs). The example's active provider is `anthropic` because
that's what this repo's `.boukensha/settings.yaml` has configured — the
other four backends are ported and importable but not exercised by
`example.py`'s default run, exactly mirroring Ruby's `example.rb`.

## Implementation steps

1. **Scaffold** `week1_baseline/python/03_prompt_builder/` per the layout
   above; copy `requirements.txt` from `02_the_registry` unchanged.
2. **`boukensha/tool.py`, `boukensha/message.py`, `boukensha/context.py`,
   `boukensha/registry.py`, `boukensha/tasks/base.py`,
   `boukensha/tasks/player.py`** — copy unchanged from `02_the_registry`.
3. **`boukensha/config.py`** — copy from `02_the_registry`'s `config.py`,
   re-add the `PROMPTS_DIR` module-level constant (see the Config directory
   resolution section). Every other line stays the same.
4. **`boukensha/errors.py`** — add `class UnsupportedModelError(Exception):
   pass` alongside the existing `UnknownToolError`.
5. **`prompts/system.md`** — copy Ruby's `prompts/system.md` verbatim
   (single line, MUD player assistant default prompt).
6. **`boukensha/backends/base.py`** — `Base` class implementing (per the
   mapping table): `models()` classmethod, `model_info_for(model)`
   classmethod, `validate_model(model)` classmethod raising
   `UnsupportedModelError`, `_configure_model(self, model)` instance helper
   setting `self.model`/`self.model_info`, and instance properties
   `context_window`, `input_token_cost_per_million`,
   `output_token_cost_per_million`, `usage_unit`, `usage_level`, plus
   `estimate_cost(self, input_tokens, output_tokens)`.
7. **`boukensha/backends/anthropic.py`** — `Anthropic(Base)`: `MODELS` dict
   (4 entries: `claude-haiku-4-5`, `claude-haiku-4-5-20251001`,
   `claude-sonnet-4-6`, `claude-opus-4-8`, verbatim prices/windows from
   Ruby); `__init__(self, api_key, model)`; `to_messages`, `to_tools`,
   `to_payload(self, context, max_output_tokens=1024)`, `headers`, `url`
   per the Ruby source.
8. **`boukensha/backends/gemini.py`** — `Gemini(Base)`: `MODELS` dict (5
   entries); `to_messages` maps `"assistant"` → `"model"` role,
   `"tool_result"` → `functionResponse` part, else default `parts:
   [{"text": ...}]`; `to_tools` wraps in `functionDeclarations` (empty list
   if no tools, matching Ruby's `return [] if tools.empty?`); `to_payload`
   builds `systemInstruction`/`contents`/`tools`/`generationConfig`; `url`
   interpolates `{model}:generateContent`.
9. **`boukensha/backends/ollama.py`** — `Ollama(Base)`: `MODELS` dict (9
   local models, all zero-cost `local_compute`); `__init__(self, model,
   host="http://localhost:11434")` (no `api_key`); two-arg
   `to_messages(self, system, messages)` prepending a system message,
   mapping `"tool_result"` → `{"role": "tool", "tool_name": ...}`; `to_tools`
   wraps in `function`-envelope; `headers` has no auth; `url` is
   `f"{self.host}/api/chat"`.
10. **`boukensha/backends/ollama_cloud.py`** — `OllamaCloud(Base)`: `MODELS`
    dict (3 cloud entries, `None` costs, `usage_unit="ollama_cloud_usage"`,
    `usage_level` set); same `to_messages`/`to_tools` shape as `Ollama.py`;
    `headers` includes `Authorization: Bearer {api_key}`; `url` is
    `f"{BASE_URL}/api/chat"`.
11. **`boukensha/backends/openai.py`** — `OpenAI(Base)`: `MODELS` dict (3
    entries: `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`); two-arg `to_messages`
    mapping `"tool_result"` → `{"role": "tool", "tool_call_id": ...}`;
    `to_tools` same `function`-envelope shape; `to_payload` uses
    `max_completion_tokens` (not `max_tokens`); `headers` includes
    `Authorization: Bearer {api_key}`.
12. **`boukensha/backends/__init__.py`** — empty or re-exports the five
    backend classes (match whichever style `boukensha/tasks/__init__.py`
    already uses in this repo).
13. **`boukensha/prompt_builder.py`** — `PromptBuilder` class per the
    mapping table: `__init__(self, context, backend)`, `to_messages`,
    `to_tools`, `to_api_payload(self, max_output_tokens=1024)`, `headers`,
    `url`.
14. **`boukensha/__init__.py`** — re-export `Config`, `Context`, `Message`,
    `Player`, `Tool`, `Registry`, `UnknownToolError`,
    `UnsupportedModelError`, `PromptBuilder`, `Anthropic`, `Gemini`,
    `Ollama`, `OllamaCloud`, `OpenAI`.
15. **`examples/example.py`** — port `example.rb` line-for-line: same
    `BOUKENSHA_DIR` fallback, build `player_settings` and `system_prompt` via
    `Player.system_prompt(..., user_prompts_dir=..., default_prompts_dir=Config.PROMPTS_DIR)`,
    construct a `Context`/`Registry`, register `look` and `move` tools
    through the registry, add the same 3 messages (`user`, `assistant`,
    `tool_result` with `tool_use_id="toolu_01X"`), print the
    `=== BOUKENSHA Step 3: Prompt Builder ===` header, resolve
    `provider`/`model` from `Player`, branch on `provider` to construct the
    matching backend (reading the matching env var per backend), build a
    `PromptBuilder`, and print `Config:`, `Provider:`, `Model:`, then
    `json.dumps(builder.to_api_payload(), indent=2)`.
16. **`week1_baseline/bin/python/03_prompt_builder`** — new bash script,
    same shape as `bin/python/02_the_registry`:
    ```bash
    #!/usr/bin/env bash

    cd "$(dirname "$0")/../../python/03_prompt_builder"
    source .venv/bin/activate
    python examples/example.py
    ```
    (`chmod +x`).
17. **`README.md`** in `python/03_prompt_builder/` — same shape as the Ruby
    README (New Files, How It Works diagram, `PromptBuilder` method table,
    Backends section incl. the per-backend model tables and cost fields,
    System Prompt / Tool Results / Tool Definitions / Message Roles JSON
    comparison blocks, Considerations, Run Example), adjusted for the Python
    venv setup steps (same as prior steps' READMEs) and the
    `model_info_for`/`model_info` naming split called out in the mapping
    table (the Ruby README doesn't need to explain this since Ruby has no
    collision — add a short note explaining the Python-specific split).
18. **Verify**: run `./week1_baseline/bin/python/03_prompt_builder` and
    confirm output matches the verified Ruby run captured above,
    field-for-field, except for the documented `Boukensha::Config` naming
    divergence already established in prior steps.

## Out of scope for this step

- No networking / no actual API calls to any of the 5 providers — this step
  only builds payloads, matching Ruby's explicit scope statement in its
  README.
- No new config keys or schema changes beyond `PROMPTS_DIR`'s reinstatement
  (which is a constant, not a settings key).
- No `pyproject.toml`/packaging, no CLI entry-point registration, no test
  suite, no `requests`/`httpx` dependency — same as prior steps.
- No fixes to rough edges already carried over from `00_config`/
  `01_struct_skeleton`/`02_the_registry` (`.yml` extension question,
  missing-settings-file handling, `Context`/`Registry`'s dual ownership of
  tools).
- No exercising of the four non-configured backends (`Gemini`, `Ollama`,
  `OllamaCloud`, `OpenAI`) in `example.py` beyond being importable and
  correctly implemented — `example.py`'s live run only builds a payload for
  whichever provider `.boukensha/settings.yaml` currently configures
  (`anthropic` in this repo), exactly mirroring Ruby's `example.rb`.
</content>
