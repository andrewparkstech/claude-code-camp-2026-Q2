# The Tool Registry (Python port)

Python port of `week1_baseline/ruby/02_the_registry`. Same behavior, same
output shape (aside from the display divergences noted below) — builds on
the `Tool`/`Message`/`Context` code ported in `python/01_struct_skeleton`,
adding the piece that manages what capabilities the agent can use.

It has two jobs:
  1. storing tools
  2. dispatching tools when asked

## Setup

```bash
cd week1_baseline/python/02_the_registry
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## New Files

| File | Description |
|---|---|
| `boukensha/registry.py` | The Registry class — registers tools and dispatches calls |
| `boukensha/errors.py` | BOUKENSHA-specific error classes |

## How It Works

The agent NEVER calls a tool directly.
It emits a structured request (name and args) and the Registry looks up the tool and runs it.

```
Agent:  "Hey registry call move with direction='north'"
Registry: "looking up "move" in the tool table"
Registry: "Found it now calling the block with the provided args"
Registry: "Here's the result"
Agent: "Thanks buddy"
Registry: "Thats why you pay me the big tokens"
```

## Registry

| Method | Description |
|---|---|
| `tool(name, description, parameters=None, block=None)` | Registers a new tool on the context |
| `dispatch(name, args=None)` | Looks up a tool by name and calls it with the provided args |

## UnknownToolError

Raised when `dispatch` is called with a name that has no registered tool.
A harness needs explicit error boundaries — an unrecognised tool name should never silently fail.

**Example:**
```
UnknownToolError: No tool registered as 'flee'
```

## Run Example

```bash
./week1_baseline/bin/python/02_the_registry
```

Expected output (values from your `.boukensha/`):

```
=== BOUKENSHA Step 2: Tool Registry ===

Config:  #<Boukensha::Config dir=/home/andrew/Sites/Claude-Code-Camp/.boukensha tasks=player>
Context: #<Context task=player turns=0 tools=2>
Tools:
  #<Tool name=move description=Move the player in a direction (north, so params=['direction']>
  #<Tool name=shout description=Shout a message so everyone in the zone c params=['message']>

Dispatching 'shout' with message='dragon spotted'...
Result: DRAGON SPOTTED

Dispatching 'move' with direction='north'...
Result: You move north into a torch-lit corridor.

UnknownToolError caught: No tool registered as 'flee'
```

This is the *actual* output of both the Ruby and Python versions — the Ruby
README's own "Expected Output" section is stale (it shows a `budget=8192`
field on `Context` that doesn't exist in `context.rb`, and untruncated tool
descriptions). That stale text wasn't carried over here; this block was
captured by running `./week1_baseline/bin/ruby/02_the_registry` directly.

## Ruby → Python idiom differences

- `dispatch` in Ruby converts string-keyed args to symbol keys
  (`args.transform_keys(&:to_sym)`) before calling the block, because Ruby
  blocks take keyword args as symbols while dispatched args arrive as
  string-keyed JSON. Python has no symbol/string duality — `**args` already
  binds string keys directly to a function's keyword parameters — so this
  port has nothing to translate. The Ruby README's "Considerations" section
  about this gotcha is intentionally not carried over here; it doesn't apply.
- Ruby's `&block` / `do...end` syntax has no Python equivalent. `Registry.tool`
  takes the callable as an explicit `block=` keyword argument instead.
- `parameters: {}` and `args = {}` Ruby default arguments become
  `parameters=None` / `args=None` in Python, defaulted to `{}` inside the
  method body — avoids Python's mutable-default-argument pitfall while
  keeping identical per-call behavior.
- `Tool#parameters.keys` prints as `[:direction]` in Ruby (symbol keys) vs
  `['direction']` in Python (string keys) — same display divergence already
  noted in the `01_struct_skeleton` port.

## Considerations

We now register tools with the Registry but our code still has direct registration and tools in context. This likely should have been reworked.

Checking the final baseline example, we did correct the issue.
The context should have reference to tools[] its currently using, and the full table of tools registered should live on the Registry.

We'll correct this manually in a future step and we will leave things place.
