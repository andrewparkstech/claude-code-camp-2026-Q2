# 00 · Configuration (Python port)

Python port of `week1_baseline/ruby/00_config`. Same behavior, same
`.boukensha/settings.yaml` schema, same output — a single `.boukensha/`
directory works for either language version.

We want to be able to manage all configuration from an external file, e.g.
`~/.boukensha/settings.yaml`, via a dedicated `Config` class. As we add
configuration in each iteration we will be updating the configuration schema
and class.

Configuration is organised by **task** — a role in the agentic loop bound to
its own LLM. week1_baseline only drives a single `player` task (the main
loop), but a more advanced loop will assign different LLMs to different
tasks. A task is either a "single-task" or a "multi-task" — the latter being
a full agent.

## Design Considerations

We keep dependencies minimal: `PyYAML` (to read `settings.yaml` — Python's
standard library has no YAML parser) and `python-dotenv` (to load `.env`
files), the Python equivalents of the Ruby version's `dotenv` gem.

## Code Changes

| File | Purpose |
|------|---------|
| `boukensha/config.py` | `Config` class |
| `boukensha/tasks/base.py` | abstract `Base` task (provider/model + prompt resolution) |
| `boukensha/tasks/player.py` | concrete `Player` task (the main loop) |
| `boukensha/__init__.py` | top-level package exports |
| `prompts/system.md` | default system prompt shipped with the library |
| `examples/example.py` | runnable smoke-test |

---

## Setup

```bash
cd week1_baseline/python/00_config
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Config directory resolution

The `Config` class looks for a `.boukensha/` directory in this order:

1. **`BOUKENSHA_DIR` env var** — set this to point at any directory you like.
2. **`~/.boukensha`** — the default location for a real install.

## Config directory structure

The class expects the following:

```
.boukensha/
  .env                 # stores credentials eg. LLMs APIs (never committed to repo)
  settings.yaml        # all non-secret settings
  prompts/
    <task>/
      system.md        # per-task override for the default system prompt (optional)
```

---

## Tasks

`Base` is an abstract stateless class. All behaviour is expressed as
classmethods that accept a `settings` dict — no instances are created.
Concrete subclasses define `.task_name()`. For now only `Player` exists;
future steps add per-turn ceilings (`max_iterations`, `max_turn_tokens`,
`max_output_tokens`, `compaction_threshold`) — these are **not** read yet.

`Config.tasks()` returns the raw dict from `settings.yaml` under `tasks:`.
Pass a name to look up a specific task's settings dict, then pass it to the
stateless class:

```python
Player.provider(config.tasks("player"))
Player.system_prompt(
    config.tasks("player"),
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=PROMPTS_DIR,
)
```

## System prompt resolution

Per task, `Player.system_prompt` is resolved in this order:

1. **`.boukensha/prompts/<task>/system.md`** — used when the task's
   `prompt_override.system` is `true` and the file exists.
2. **`prompts/system.md`** — the default system prompt shipped with the library.

## Configuration Schema

The following properties so far:
- `tasks`: a map of task name → task config (provider, model, prompt_override).
- `tasks.<name>.prompt_override.system`: when `true`, the task's
  `.boukensha/prompts/<name>/system.md` overrides the default system prompt.
- `mud`: MUD connection information for the main player.

```yaml
tasks:
  player:
    provider: anthropic        # provider name (string)
    model: claude-haiku-4-5
    prompt_override:
      system: true
mud:
  host: localhost
  port: 4000
  username: dummy
  password: helloworld
```

## Run Example

```bash
./week1_baseline/bin/00_config_python
```

Expected output (values from your `.boukensha/`):

```
=== Boukensha Step 0: Configuration ===

Config dir:     /home/andrew/Sites/Claude-Code-Camp/.boukensha
Tasks:          player

-- player task --
Provider:       anthropic
Model:          claude-haiku-4-5
Prompt override?true
System prompt:  You are a MUD player assistant. Use the tools available to y...

MUD host:       localhost:4000
MUD user:       dummy

API key set?    true

#<Boukensha::Config dir=/home/andrew/Sites/Claude-Code-Camp/.boukensha tasks=player>
```

## Considerations

These are things we observed but we do not want fixed since future steps will
break them anyway — kept identical to the Ruby version for parity:
- We have a default prompt, e.g. `prompts/system.md`; it's supposed to be
  scoped on task, e.g. `prompts/<task>/system.md`.
- Our settings file should accept `.yml` or `.yaml`; right now it only takes
  `.yaml`.
- We don't have a graceful way of saying we didn't find the file — it just
  errors out expecting to read a non-existent file.

## Ruby → Python idiom differences

A few Ruby idioms don't map 1:1 and are intentionally simplified rather than
reproduced:
- Ruby's `dig`/`tasks` look up both string and symbol keys
  (`node[key.to_s] || node[key.to_sym]`). PyYAML never produces non-string
  keys, so the Python port only looks up `str(key)`.
- Ruby's `prompt_override?` becomes `prompt_override` — Python has no
  `?`-suffixed method convention.
- Ruby's private class methods become `_`-prefixed module-level helper
  functions in `base.py` — Python has no true `private`.
