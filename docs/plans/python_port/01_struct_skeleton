# Python Port Plan · 01_struct_skeleton

Port `week1_baseline/ruby/01_struct_skeleton` to
`week1_baseline/python/01_struct_skeleton`, preserving behavior and output
shape exactly (module-name-in-string differences aside — see the mapping
table). This step adds three new data structures — `Tool`, `Message`,
`Context` — on top of the config/tasks code already ported in
[00_config](00_config). It's a straight port of the current step only: no new
config keys, no fixes to the known rough edges already carried over from
`00_config`.

## Decisions (confirmed with user)

- **Struct equivalent**: Ruby's `Struct.new(...) do ... end` (used for `Tool`
  and `Message`) becomes a stdlib `@dataclass` in Python — mutable, minimal
  boilerplate, in the same spirit as Ruby's lightweight Struct, and it keeps
  the "stdlib only" philosophy established in the `00_config` port. Each
  dataclass gets a hand-written `__str__` to match the Ruby `to_s` format
  (dataclass's auto-generated `__repr__` is not used for the display format,
  since it doesn't match the `#<...>` shape).
- **Code reuse**: `python/01_struct_skeleton` is a fully self-contained
  directory, duplicating `config.py` and `tasks/` from `python/00_config`
  rather than importing across step directories — this mirrors both the Ruby
  original (each `ruby/NN_step` is its own snapshot; `01_struct_skeleton`
  does not `require` from `../00_config`) and the precedent already set by
  the `00_config` Python port.
- **Tooling / tests**: same as `00_config` — plain `venv` + `requirements.txt`
  (`PyYAML`, `python-dotenv`), no test suite (the Ruby version has none;
  verification is the manual `examples/example.py` smoke test).
- **Entry point**: `week1_baseline/bin/python/01_struct_skeleton`, matching
  the `bin/python/00_config` / `bin/ruby/01_struct_skeleton` naming already
  in place (the original `00_config` plan proposed `bin/00_config_python`,
  but the repo has since settled on the `bin/<lang>/<step>` layout — this
  plan follows the layout actually on disk).

## Target directory layout

```
week1_baseline/python/01_struct_skeleton/
  requirements.txt          # PyYAML, python-dotenv (same as 00_config)
  README.md                 # same shape as the Ruby README, Python-specific run example
  boukensha/
    __init__.py              # re-exports Config, Player, Tool, Message, Context
    config.py                # ported from 00_config, PROMPTS_DIR constant dropped (see mapping table)
    tool.py                  # Tool dataclass
    message.py               # Message dataclass
    context.py                # Context class
    tasks/
      __init__.py
      base.py                # unchanged port from 00_config (Ruby base.rb is identical between steps)
      player.py               # unchanged port from 00_config
  examples/
    example.py                 # smoke test, same shape as example.rb

week1_baseline/bin/python/01_struct_skeleton   # new — parallel to bin/python/00_config
```

## Ruby → Python mapping

| Ruby | Python | Notes |
|---|---|---|
| `Tool = Struct.new(:name, :description, :parameters, :block)` | `@dataclass class Tool: name: str; description: str; parameters: dict; block: Callable` | positional fields in the same order; `block` typed `Callable[..., str]` |
| `Message = Struct.new(:role, :content, :tool_use_id)` | `@dataclass class Message: role: str; content: str; tool_use_id: str \| None = None` | `tool_use_id` keeps its default of `None`, matching Ruby's Struct default of `nil` for a trailing unset field |
| `Tool#to_s` (`description.to_s[0..40]`) | `Tool.__str__` using `(self.description or "")[:41]` | Ruby's inclusive `0..40` range is 41 characters — use Python slice `[:41]`, not `[:40]` |
| `Message#to_s` (`content.to_s[0..60]`) | `Message.__str__` using `(self.content or "")[:61]` | same off-by-one care: `0..60` inclusive = 61 chars → `[:61]` |
| `parameters.keys` printed as `[:direction]` | `list(self.parameters.keys())` printed as `['direction']` | **display divergence, not a bug**: the Ruby example uses symbol keys (`{ direction: {...} }`); Python's `Tool` uses string keys (`{"direction": {...}}`), which is the idiomatic dict-as-JSON-schema shape. Document this in the README's example block rather than trying to fake symbol-style output. |
| `Context#initialize(task:, system: nil)` | `Context.__init__(self, task, system=None)` | `messages = []`, `tools = {}` initialized fresh per instance (same as Ruby) |
| `Context#register_tool(tool)` | `Context.register_tool(self, tool)` | `self.tools[tool.name] = tool` |
| `Context#add_message(role, content, tool_use_id: nil)` | `Context.add_message(self, role, content, tool_use_id=None)` | appends a `Message(role, content, tool_use_id)` |
| `def tool_count = @tools.size` / `def turn_count = @messages.size` | `@property def tool_count(self)` / `@property def turn_count(self)` | Ruby's endless-method no-arg query style maps to Python `@property`, consistent with how `mud_host` etc. became properties in the `00_config` port |
| `task&.task_name` in `Context#to_s` | `self.task.task_name() if self.task else None` | `task` is the *class* itself (e.g. `Player`, not an instance) in both languages; `task_name` is a classmethod call in Python, a class-level method call in Ruby |
| `Context#to_s` → `"#<Context task=... turns=... tools=...>"` | `Context.__str__` → same string | no `Boukensha::` prefix in Ruby's `Context#to_s` either — keep it exactly as `#<Context ...>`, unlike `Config#to_s` which does keep `Boukensha::Config` (see the `00_config` mapping table, which chose to keep that string byte-identical) |
| `PROMPTS_DIR = File.expand_path("../../prompts", __dir__)` (dropped in Ruby's `01_struct_skeleton/lib/boukensha/config.rb`, present in `00_config`'s) | drop the `PROMPTS_DIR` module constant from `config.py` in this step | mirrors the Ruby diff exactly; `01_struct_skeleton`'s `example.rb` calls `system_prompt` without `default_prompts_dir:`, so nothing downstream depends on it — confirmed by running the Ruby example, whose output never prints the system prompt at all in this step |
| `lib/boukensha.rb` (`require_relative "boukensha/tool"` etc.) | `boukensha/__init__.py` | adds `Tool`, `Message`, `Context` to the re-exports already present from `00_config` (`Config`, `Player`) |
| `ctx.add_message(:user, ...)` / `:assistant` | `ctx.add_message("user", ...)` / `"assistant"` | Ruby symbols stringify without a leading colon in interpolation (`role=user`), so plain Python strings produce identical output |

`Tasks::Base` and `Tasks::Player` are byte-identical between the Ruby
`00_config` and `01_struct_skeleton` directories (confirmed via `diff`) — port
`base.py`/`player.py` by copying them unchanged from the `00_config` Python
port, no re-derivation needed.

## Config directory resolution (unchanged)

Same as `00_config`: `BOUKENSHA_DIR` env var, else `~/.boukensha`, resolved
via `pathlib`. No changes in this step.

## Config schema (unchanged)

No new keys. Same `settings.yaml` shape as `00_config`.

## Implementation steps

1. **Scaffold** `week1_baseline/python/01_struct_skeleton/` per the layout
   above; copy `requirements.txt` from `00_config` unchanged.
2. **`boukensha/config.py`** — copy from `00_config`'s `config.py`, then
   remove the `PROMPTS_DIR` module constant (per the mapping table). Every
   other line stays the same.
3. **`boukensha/tasks/base.py`, `boukensha/tasks/player.py`** — copy
   unchanged from `00_config`.
4. **`boukensha/tool.py`** — `Tool` dataclass with `name`, `description`,
   `parameters`, `block` fields and a `__str__` matching Ruby's `to_s`
   format (41/61-char slices per the mapping table).
5. **`boukensha/message.py`** — `Message` dataclass with `role`, `content`,
   `tool_use_id=None` and a matching `__str__` (optional `[tool_use_id]` tag).
6. **`boukensha/context.py`** — `Context` class: `__init__(task, system=None)`
   setting up empty `messages`/`tools`; `register_tool`; `add_message`;
   `tool_count`/`turn_count` properties; `__str__`.
7. **`boukensha/__init__.py`** — re-export `Config`, `Player`, `Tool`,
   `Message`, `Context`.
8. **`examples/example.py`** — port `example.rb` line-for-line: same
   `BOUKENSHA_DIR` fallback, build a `Context` for `Player`, register the
   `move` `Tool` with a `lambda direction: f"You move {direction} into a
   torch-lit corridor."` block, add the same two messages, print the same
   labeled lines in the same order.
9. **`week1_baseline/bin/python/01_struct_skeleton`** — new bash script,
   same shape as `bin/python/00_config`:
   ```bash
   #!/usr/bin/env bash

   cd "$(dirname "$0")/../python/01_struct_skeleton"
   source .venv/bin/activate
   python examples/example.py
   ```
   (`chmod +x`).
10. **`README.md`** in `python/01_struct_skeleton/` — same shape as the Ruby
    README (Data Structures section for `Tool`/`Message`/`Context` with
    examples, Run Example section), adjusted for the Python venv setup steps
    (same as `00_config`'s README) and the `params=['direction']` vs
    `params=[:direction]` display divergence noted in the mapping table.
11. **Verify**: run `./week1_baseline/bin/python/01_struct_skeleton` and
    confirm output matches the Ruby run
    (`./week1_baseline/bin/ruby/01_struct_skeleton`) field-for-field, except
    for the documented `Boukensha::Config` naming and `params=[...]`
    formatting divergences already called out above.

## Out of scope for this step

- No new config keys or schema changes.
- No `pyproject.toml`/packaging, no CLI entry-point registration, no test
  suite — same as `00_config`.
- No fixes to the rough edges already carried over from `00_config`
  (`.yml` extension, missing-settings-file handling, task-scoped default
  prompts dir).
- No behavior for actually *using* the registered tool's `block` beyond
  storing/printing it — invocation is a later step's concern.
</content>
