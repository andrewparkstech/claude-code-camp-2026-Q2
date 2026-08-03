# Python Port Plan · 02_the_registry

Port `week1_baseline/ruby/02_the_registry` to
`week1_baseline/python/02_the_registry`, preserving behavior and output shape
exactly (module-name-in-string differences aside — see the mapping table).
This step adds a `Registry` class and an `UnknownToolError` on top of the
`Tool`/`Message`/`Context` structures already ported in
[01_struct_skeleton](01_struct_skeleton). It's a straight port of the current
step only: no new config keys, no fixes to the known rough edges already
carried over from `00_config`/`01_struct_skeleton`.

## Decisions (confirmed with user)

- **Stale README output**: the Ruby README's "Expected Output" block does not
  match what `ruby/02_the_registry/examples/example.rb` actually prints
  (verified by running `./week1_baseline/bin/ruby/02_the_registry`) — it
  shows a `budget=8192` field on `Context` that doesn't exist anywhere in
  `context.rb`, and shows the full untruncated tool description in quotes
  instead of the real 41-char truncation. The Python port's README documents
  the **actual verified output**, not the stale text. This is a Ruby-doc bug,
  not a behavior difference to reconcile — it isn't fixed in the Ruby README
  either, it's just not propagated into the new copy.
- Everything else follows the precedent already set by `00_config` and
  `01_struct_skeleton`: self-contained per-step directory (duplicate
  `config.py`/`tasks/` rather than import across step directories), plain
  `venv` + `requirements.txt` (`PyYAML`, `python-dotenv`), no test suite (the
  Ruby version has none), entry point at `week1_baseline/bin/python/02_the_registry`.

## Target directory layout

```
week1_baseline/python/02_the_registry/
  requirements.txt          # PyYAML, python-dotenv (same as 01_struct_skeleton)
  README.md                 # same shape as the Ruby README, Python-specific run example,
                             # Expected Output section uses verified real output (see Decisions)
  boukensha/
    __init__.py              # re-exports Config, Context, Message, Player, Tool, Registry, UnknownToolError
    config.py                # unchanged port from 01_struct_skeleton (Ruby config.rb is byte-identical between steps)
    tool.py                  # unchanged port from 01_struct_skeleton
    message.py               # unchanged port from 01_struct_skeleton
    context.py               # unchanged port from 01_struct_skeleton (see mapping table note on the stray Ruby comment)
    errors.py                # new — UnknownToolError
    registry.py               # new — Registry class
    tasks/
      __init__.py
      base.py                # unchanged port from 01_struct_skeleton
      player.py               # unchanged port from 01_struct_skeleton
  examples/
    example.py                 # smoke test, same shape as example.rb

week1_baseline/bin/python/02_the_registry   # new — parallel to bin/python/01_struct_skeleton
```

`config.py`, `tool.py`, `message.py`, `tasks/base.py`, `tasks/player.py` are
byte-identical in Ruby between `01_struct_skeleton` and `02_the_registry`
(confirmed via `diff`) — copy the Python versions from `01_struct_skeleton`
unchanged, no re-derivation needed. `context.rb` has one extra line in
`02_the_registry` — a stray, unfinished comment (`# This isn'`) that reads as
an editing artifact, not real content. It's not carried into `context.py`,
consistent with how earlier steps already didn't port Ruby comments verbatim.

## Ruby → Python mapping

| Ruby | Python | Notes |
|---|---|---|
| `Boukensha::UnknownToolError < StandardError` | `class UnknownToolError(Exception)` | Ruby's `StandardError` is the idiomatic "normal, catchable error" base; Python's equivalent is `Exception` directly — no custom hierarchy needed for one error class |
| `Registry#initialize(context)` | `Registry.__init__(self, context)` | `self.context = context`, same as Ruby's `@context` |
| `tool(name, description:, parameters: {}, &block)` | `tool(self, name, description, parameters=None, block=None)` | Ruby's `&block`/`do...end` has no Python equivalent — pass the callable as an explicit `block=` keyword, matching how `Tool`'s `block` field was already ported as a plain callable in `01_struct_skeleton` |
| `parameters: {}` default | `parameters=None` → `parameters or {}` internally | avoids the classic Python mutable-default-argument pitfall; behavior is identical to Ruby's fresh `{}` per call |
| `Tool.new(name.to_s, description, parameters, block)` | `Tool(str(name), description, parameters or {}, block)` | same coercion of `name` to a string |
| `@context.register_tool(tool)` then `tool` returned | `self.context.register_tool(tool)` then `return tool` | same return-the-tool behavior |
| `dispatch(name, args = {})` | `dispatch(self, name, args=None)` → `args = args or {}` | same mutable-default-argument fix as `tool()` |
| `@context.tools[name.to_s]` | `self.context.tools.get(str(name))` | |
| `raise UnknownToolError, "No tool registered as '#{name}'" unless tool` | `if tool is None: raise UnknownToolError(f"No tool registered as '{name}'")` | same message format |
| `tool.block.call(**args.transform_keys(&:to_sym))` | `return tool.block(**args)` | **behavior simplification, same idiom as the `dig()` note in `00_config`**: Ruby needs `transform_keys(&:to_sym)` because blocks take keyword args as symbols but dispatched args arrive as string-keyed JSON. Python has no symbol/string duality — `**dict` unpacking with string keys already binds to a function's keyword parameters, so the conversion step is dropped entirely, not reimplemented as a no-op. |
| `lib/boukensha.rb` (`require_relative "boukensha/errors"`, `"boukensha/registry"`) | `boukensha/__init__.py` | adds `Registry`, `UnknownToolError` to the re-exports already present from `01_struct_skeleton` |
| README "Considerations" section on string/symbol key translation | dropped from the Python README's Considerations | the whole gotcha it describes is Ruby-specific (see the `dispatch` row above) — it doesn't exist in Python, so there's nothing to make "visible for learning purposes" in this port; note its absence is intentional, not an oversight |

## Config directory resolution (unchanged)

Same as `01_struct_skeleton`: `BOUKENSHA_DIR` env var, else `~/.boukensha`,
resolved via `pathlib`. No changes in this step.

## Config schema (unchanged)

No new keys. Same `settings.yaml` shape as `00_config`/`01_struct_skeleton`.

## Verified Ruby output (source of truth for this port)

Captured by running `./week1_baseline/bin/ruby/02_the_registry` against the
repo's existing `.boukensha/` directory — this is what the Python port's
output must match field-for-field (adjusted only for `Boukensha::Config` →
`Config` naming, per prior steps' precedent):

```
=== BOUKENSHA Step 2: Tool Registry ===

Config:  #<Boukensha::Config dir=/path/to/.boukensha tasks=player>
Context: #<Context task=player turns=0 tools=2>
Tools:
  #<Tool name=move description=Move the player in a direction (north, so params=[:direction]>
  #<Tool name=shout description=Shout a message so everyone in the zone c params=[:message]>

Dispatching 'shout' with message='dragon spotted'...
Result: DRAGON SPOTTED

Dispatching 'move' with direction='north'...
Result: You move north into a torch-lit corridor.

UnknownToolError caught: No tool registered as 'flee'
```

(Ruby's `params=[:direction]` becomes Python's `params=['direction']` in the
Python run — same string-vs-symbol display divergence already documented and
accepted in the `01_struct_skeleton` plan.)

## Implementation steps

1. **Scaffold** `week1_baseline/python/02_the_registry/` per the layout
   above; copy `requirements.txt` from `01_struct_skeleton` unchanged.
2. **`boukensha/config.py`, `boukensha/tool.py`, `boukensha/message.py`,
   `boukensha/tasks/base.py`, `boukensha/tasks/player.py`** — copy unchanged
   from `01_struct_skeleton`.
3. **`boukensha/context.py`** — copy unchanged from `01_struct_skeleton`
   (the one-line stray comment in Ruby's `02_the_registry/context.rb` is not
   ported; see the mapping table note).
4. **`boukensha/errors.py`** — `class UnknownToolError(Exception): pass`.
5. **`boukensha/registry.py`** — `Registry` class: `__init__(self, context)`;
   `tool(self, name, description, parameters=None, block=None)` building a
   `Tool`, calling `self.context.register_tool(tool)`, returning it;
   `dispatch(self, name, args=None)` looking up `self.context.tools`,
   raising `UnknownToolError` on a miss, else calling `tool.block(**args)`.
6. **`boukensha/__init__.py`** — re-export `Config`, `Context`, `Message`,
   `Player`, `Tool`, `Registry`, `UnknownToolError`.
7. **`examples/example.py`** — port `example.rb` line-for-line: same
   `BOUKENSHA_DIR` fallback, build a `Context` for `Player`, create a
   `Registry(ctx)`, register `move` and `shout` tools through
   `registry.tool(...)` (not direct `Tool(...)` construction, matching the
   Ruby example's point that tools now go through the registry), print the
   same labeled lines in the same order, dispatch `shout` then `move`
   successfully, then dispatch `flee` inside a `try/except UnknownToolError`
   and print the caught message.
8. **`week1_baseline/bin/python/02_the_registry`** — new bash script, same
   shape as `bin/python/01_struct_skeleton`:
   ```bash
   #!/usr/bin/env bash

   cd "$(dirname "$0")/../../python/02_the_registry"
   source .venv/bin/activate
   python examples/example.py
   ```
   (`chmod +x`).
9. **`README.md`** in `python/02_the_registry/` — same shape as the Ruby
   README (New Files, How It Works, `Registry`/`UnknownToolError` method
   tables, Expected Output, Run Example), adjusted for:
   - Python venv setup steps (same as prior steps' READMEs)
   - Expected Output section using the **verified actual output** captured
     above, not the stale Ruby README text (per the Decisions section)
   - dropping the string/symbol-key "Considerations" note (per the mapping
     table — doesn't apply to Python)
   - keeping the duplicate-looking "## Considerations" section at the bottom
     of the Ruby README (the note about tools living on both `Context` and
     `Registry`, to be reworked later) — carry that content forward as-is,
     it's a real forward-looking note about the codebase's design, not a doc
     bug like the Expected Output block.
10. **Verify**: run `./week1_baseline/bin/python/02_the_registry` and confirm
    output matches the verified Ruby run field-for-field, except for the
    documented `Boukensha::Config` naming and `params=[...]` formatting
    divergences already established in prior steps.

## Out of scope for this step

- No new config keys or schema changes.
- No `pyproject.toml`/packaging, no CLI entry-point registration, no test
  suite — same as prior steps.
- No fixes to the rough edges already carried over from `00_config` (`.yml`
  extension, missing-settings-file handling, task-scoped default prompts
  dir).
- No reworking `Context`/`Registry`'s dual ownership of tools — the Ruby
  README's closing "Considerations" note flags this as a known issue to
  correct in a later step, in both languages. This port keeps the same
  direct-registration-plus-registry duplication Ruby has today.
</content>
