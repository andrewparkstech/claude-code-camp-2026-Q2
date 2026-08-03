# Python Port Plan · 00_config

Port `week1_baseline/ruby/00_config` to `week1_baseline/python/00_config`,
preserving behavior, schema, and output exactly. This is a straight port of
the current step only — do not add the `max_iterations` / per-turn-ceiling
fields the Ruby README flags as "not read yet," and do not fix the three
known rough edges listed in the Ruby README's "Considerations" section
(`.yml` not accepted, no graceful missing-settings-file error, prompts dir
not task-scoped). Those stay broken in both languages until a later step
addresses them in both.

## Decisions (confirmed with user)

- **YAML parsing**: add `PyYAML` as a dependency — the Python-stdlib
  equivalent of the Ruby version's one deliberate exception (`dotenv`).
  `settings.yaml` keeps its current format/schema so a single `.boukensha/`
  directory works for both language versions.
- **Env files**: add `python-dotenv`, mirroring the Ruby `dotenv` gem.
- **Tooling**: plain `venv` + `requirements.txt`. No `pyproject.toml` /
  build backend / lockfile for this step — closer in spirit to the Ruby
  version's lightweight `Gemfile`. (Note: this diverges from
  `week0_explore/circlemud-world-parser`, which uses `uv` + `pyproject.toml`;
  that's fine, this is a separate sub-project.)
- **Entry point**: add a new `week1_baseline/bin/00_config_python` script.
  Leave the existing `week1_baseline/bin/00_config` (Ruby) untouched — both
  implementations stay independently runnable.
- **Tests**: none. The Ruby version has no test suite; mirror it exactly.
  Verification is the same manual smoke-test (`examples/example.py`) the
  Ruby README documents.

## Target directory layout

```
week1_baseline/python/00_config/
  requirements.txt          # PyYAML, python-dotenv
  README.md                 # same shape as the Ruby README, Python-specific setup steps
  boukensha/
    __init__.py              # re-exports Config, Tasks.Player (mirrors lib/boukensha.rb)
    config.py                # Config class
    tasks/
      __init__.py
      base.py                # Base task class
      player.py               # Player(Base)
  prompts/
    system.md                 # copy of the Ruby default system prompt, verbatim
  examples/
    example.py                 # smoke test, same output shape as example.rb

week1_baseline/bin/00_config_python   # new — parallel to bin/00_config
```

## Ruby → Python mapping

| Ruby | Python | Notes |
|---|---|---|
| `Boukensha::Config` | `boukensha.config.Config` | same public surface |
| `Boukensha::Tasks::Base` | `boukensha.tasks.base.Base` | stateless — Python `classmethod`s, no instances, same as Ruby's class-method-only design |
| `Boukensha::Tasks::Player` | `boukensha.tasks.player.Player(Base)` | overrides `task_name` |
| `lib/boukensha.rb` (top-level require) | `boukensha/__init__.py` | imports `Config` and `Player` so `examples/example.py` can do `from boukensha import Config` / `from boukensha.tasks.player import Player` |
| `attr_reader :dir, :settings` | read-only instance attributes (`self.dir`, `self.settings` set once in `__init__`) | no need for `@property` machinery — nothing recomputes them |
| `ENV.fetch("BOUKENSHA_DIR", nil) \|\| DEFAULT_DIR` | `os.environ.get("BOUKENSHA_DIR") or DEFAULT_DIR` | same precedence |
| `YAML.safe_load(...)` | `yaml.safe_load(...)` | PyYAML |
| `Dotenv.load(env_file)` | `dotenv.load_dotenv(env_file)` | python-dotenv |
| `dig(*keys)` with `node[key.to_s] \|\| node[key.to_sym]` | `dig(*keys)` walking `dict.get(str(key))` only | **behavior simplification**: YAML parsed by PyYAML never produces non-string keys, so there is no symbol/string duality to resolve — document this as an intentional idiom difference, not a bug |
| `tasks(name = nil)` with `all[name.to_s] \|\| all[name.to_sym]` | `tasks(name=None)` using `all.get(str(name))` | same reasoning as `dig` |
| `prompt_override?(settings, prompt = :system)` | `prompt_override(settings, prompt="system")` | Python has no `?`-suffixed method convention; drop the suffix, keep the boolean-returning behavior |
| `self.task_name` raising `NotImplementedError` in Base | `classmethod task_name()` raising `NotImplementedError` in Base | same abstract-method pattern |
| private class methods (`fetch`, `read_user_prompt`, `read_default_prompt`, `read_file`) | module-level `_`-prefixed helper functions in `base.py` (or `@staticmethod` with leading underscore) | Python has no true `private`; leading underscore + keeping them out of `__all__` is the idiomatic equivalent |
| `File.exist?(path) ? File.read(path).strip : nil` | `path.read_text().strip() if path.exists() else None` | use `pathlib.Path` throughout instead of `File`/`Pathname` mixing |
| `#<Boukensha::Config dir=... tasks=...>` (`to_s`/`inspect`) | `__str__`/`__repr__` returning the same format | keep output byte-identical for the smoke test |

## Config directory resolution (unchanged)

Same two-step resolution as Ruby, implemented with `pathlib`:

1. `BOUKENSHA_DIR` env var (read before `.env` is loaded, same as Ruby).
2. `Path.home() / ".boukensha"` default.

`PROMPTS_DIR` (default prompts shipped with the library) resolves relative
to `config.py`'s own location — `Path(__file__).resolve().parent.parent /
"prompts"` — i.e. `python/00_config/prompts/`, the sibling of `boukensha/`,
matching how Ruby's `PROMPTS_DIR` sits next to `lib/`.

## Config schema (unchanged)

Same `settings.yaml` shape as the Ruby version — no new keys:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
mud:
  host: localhost
  port: 4000
  username: dummy
  password: helloworld
```

## Implementation steps

1. **Scaffold** `week1_baseline/python/00_config/` per the layout above;
   add `requirements.txt` with `PyYAML` and `python-dotenv` (pin loose
   major versions, no lockfile per the tooling decision).
2. **`boukensha/config.py`** — port `Config` per the mapping table:
   `__init__` resolves dir, loads `.env`, loads `settings.yaml`;
   `tasks()`, `user_prompts_dir`, `mud_host`/`mud_port`/`mud_username`/
   `mud_password`, `dig()`, `__str__`/`__repr__`.
3. **`boukensha/tasks/base.py`** — port `Base`: `task_name()` (raises),
   `provider()`, `model()`, `prompt_override()`, `prompt()`,
   `system_prompt()`, plus the private file-reading helpers.
4. **`boukensha/tasks/player.py`** — `Player(Base)` overriding
   `task_name()` to return `"player"`.
5. **`boukensha/__init__.py`** — re-export `Config` and `Player` so example
   code has a short import path.
6. **`prompts/system.md`** — copy verbatim from the Ruby version.
7. **`examples/example.py`** — port `example.rb` line-for-line: same
   `BOUKENSHA_DIR` fallback (repo-root `.boukensha`, four levels up from
   `examples/`), same printed lines and order, truncating the system prompt
   to 60 chars with `...` the same way.
8. **`week1_baseline/bin/00_config_python`** — new bash script:
   ```bash
   #!/usr/bin/env bash
   cd "$(dirname "$0")/../python/00_config"
   source .venv/bin/activate
   python examples/example.py
   ```
   (make executable, `chmod +x`).
9. **`README.md`** in `python/00_config/` — same shape as the Ruby README
   (overview, config dir resolution, directory structure, tasks, system
   prompt resolution, schema, run example with expected output, carried-over
   Considerations section), with a Python-specific setup section replacing
   the Ruby bundler steps:
   ```bash
   cd week1_baseline/python/00_config
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
10. **Verify**: run `./week1_baseline/bin/00_config_python` against the same
    `.boukensha/` directory used for the Ruby smoke test and confirm the
    output matches the Ruby run field-for-field (same provider, model,
    prompt-override flag, truncated system prompt, MUD host/user, API-key-set
    boolean, and final `repr` line — adjusted only for the `Boukensha::Config`
    → `Config` class-name difference).

## Out of scope for this step

- No `.yml`-extension support, no graceful "settings file missing" handling,
  no task-scoped default prompts dir — these are explicitly called out as
  known rough edges in the Ruby README and intentionally left alone.
- No `pyproject.toml`/packaging, no CLI entry-point registration, no test
  suite — per the tooling/testing decisions above.
- No new config keys (`max_iterations`, `max_turn_tokens`,
  `max_output_tokens`, `compaction_threshold`) — the Ruby version doesn't
  read these yet either.
</content>
