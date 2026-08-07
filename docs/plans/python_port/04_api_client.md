# Python Port Plan · 04_api_client

Port `week1_baseline/ruby/04_api_client` to `week1_baseline/python/04_api_client`,
preserving behavior and output shape exactly. This step adds a `Client` class
that takes the payload assembled by `PromptBuilder` (ported in
[03_prompt_builder](03_prompt_builder)) and sends it over HTTP, with retry
logic for transient failures and retryable status codes. It's a straight
port of the current step only: no tool-call loop yet (that's step 5, the
Agent Loop, per the Ruby README), no new config keys, no fixes to known
rough edges already carried over from earlier steps.

Confirmed via `diff -r` against `03_prompt_builder`: the only Ruby-side
changes in this step are a new `lib/boukensha/client.rb`, small edits to
`errors.rb` (new `ApiError`), `tasks/base.rb` (error-message wording + a
defensive type guard), `boukensha.rb` (require list), `config.rb`
(comment-only), a new `prompts/system.md`, and a rewritten `examples/example.rb`.
`backends/*.rb`, `tasks/player.rb`, `message.rb`, `tool.rb`, `context.rb`,
`registry.rb`, and `prompt_builder.rb` are byte-identical to `03_prompt_builder`
— copy the Python versions forward unchanged.

## Decisions (confirmed with user)

- **HTTP library: stdlib only.** Ruby's `client.rb` deliberately uses
  `net/http` instead of a gem — the README says explicitly "we are trying to
  avoid any libraries" so the HTTP call stays visible rather than hidden
  behind a library. The Python port matches that intent: `urllib.request` /
  `urllib.error` / `http.client` from the standard library, no `requests` or
  `httpx` added. `requirements.txt` stays `PyYAML` + `python-dotenv`, same as
  every prior step.
- **Live verification.** Ran `./week1_baseline/bin/ruby/04_api_client` for
  real against the repo's `.boukensha/` directory (provider `anthropic`,
  model `claude-haiku-4-5`) — a real, billed call to the Anthropic API —
  rather than only inspecting source, matching the rigor of prior steps'
  "Verified Ruby output" sections. Unlike prior steps, the response *body*
  is LLM-generated and inherently non-deterministic (a repeat run could get
  `stop_reason: "end_turn"` instead of `"tool_use"`, different text, etc.),
  so the captured output below is the source of truth for **shape/fields**,
  not for exact byte-for-byte text matching. The Python port's own live run
  during implementation will almost certainly return different response
  text — that's expected, not a bug.
- **Stale README tables, same as `02_the_registry`'s precedent.** Ruby's
  `04_api_client/README.md` "New Files" table lists `backends/base.rb`,
  `tasks/base.rb`, `tasks/player.rb`, and `prompts/system.md` as new, and its
  "Updated Files" table says `backends/*.rb` "now own supported model
  tables" — none of that is true for this diff (`diff -rq` against
  `03_prompt_builder` shows those files are byte-identical; the model tables
  were already added back in `03_prompt_builder`). The README reads like
  leftover text from an earlier draft of the step sequence. This plan
  documents the actual diff-verified changes instead of copying those
  tables; the Python README should do the same.
- **Retry/backoff logic: straight port, not simplified.** Same
  `MAX_RETRIES = 3`, same exponential backoff formula
  (`BASE_RETRY_DELAY * 2 ** (attempt - 1)`, i.e. 0.5s/1s/2s), same retryable
  status code set (`408, 409, 429, 500, 502, 503, 504`). Ruby's
  `TRANSIENT_ERRORS` list (8 specific exception classes covering
  connection/timeout/SSL/socket failures) doesn't map class-for-class onto
  Python's exception hierarchy — `urllib.error.URLError` alone already wraps
  most connection-refused/timeout/DNS failures as its `.reason`. The Python
  port catches a tuple of `(urllib.error.URLError, TimeoutError,
  ConnectionResetError, ConnectionRefusedError, ssl.SSLError,
  http.client.HTTPException, EOFError)` — same "retry on any transient
  network-level failure" intent as Ruby's list, not a literal 1:1
  translation.
- **SSL certificates: no workaround needed.** Ruby's `client.rb` has a NOTE
  explaining it omits `ca_file` because the macOS default path
  (`/usr/lib/ssl/cert.pem`) doesn't exist on Linux/WSL2, relying on OpenSSL
  to find system certs automatically. Python's `urllib.request.urlopen`
  already uses `ssl.create_default_context()` for `https://` URLs, which
  finds system CA certs automatically on every platform — there's no
  equivalent stdlib quirk to work around, so no comment/workaround is
  ported, just plain `urlopen`.
- Everything else follows the precedent already set by `00_config` through
  `03_prompt_builder`: self-contained per-step directory (duplicate
  `boukensha/` package rather than import across step directories), plain
  `venv` + `requirements.txt`, no test suite (Ruby has none), entry point
  script at `week1_baseline/bin/python/04_api_client`.

## Target directory layout

```
week1_baseline/python/04_api_client/
  requirements.txt          # PyYAML, python-dotenv (unchanged — no HTTP lib added, see Decisions)
  README.md                 # same shape as Ruby's, Expected Output uses actual verified run (see Decisions)
  prompts/
    system.md                # NEW content — "Boukensha, an autonomous player..." (differs from 03's MUD-flavored text)
  boukensha/
    __init__.py              # re-exports adds Client
    config.py                # unchanged port from 03_prompt_builder (Ruby's diff is comment-only)
    tool.py                  # unchanged port from 03_prompt_builder
    message.py               # unchanged port from 03_prompt_builder
    context.py                # unchanged port from 03_prompt_builder
    errors.py                # adds ApiError alongside UnknownToolError, UnsupportedModelError
    registry.py               # unchanged port from 03_prompt_builder
    prompt_builder.py         # unchanged port from 03_prompt_builder
    client.py                 # NEW — Client class
    tasks/
      __init__.py
      base.py                # small update — settings-is-a-dict guard in _fetch (see mapping table)
      player.py               # unchanged port from 03_prompt_builder
    backends/
      __init__.py
      base.py                # unchanged port from 03_prompt_builder
      anthropic.py            # unchanged port from 03_prompt_builder
      gemini.py                # unchanged port from 03_prompt_builder
      ollama.py                 # unchanged port from 03_prompt_builder
      ollama_cloud.py           # unchanged port from 03_prompt_builder
      openai.py                 # unchanged port from 03_prompt_builder
  examples/
    example.py                 # rewritten — read_file/list_directory tools, calls client.call(), prints raw response

week1_baseline/bin/python/04_api_client   # new — parallel to bin/python/03_prompt_builder
```

## Ruby → Python mapping

| Ruby | Python | Notes |
|---|---|---|
| `Boukensha::ApiError < StandardError` | `class ApiError(Exception)` | same treatment as `UnknownToolError`/`UnsupportedModelError` — no custom hierarchy |
| `Client#initialize(builder)` | `Client.__init__(self, builder)` | `self.builder = builder` |
| `Net::HTTP::Post.new(uri, @builder.headers)` / `request.body = ...to_json` | `urllib.request.Request(self.builder.url, data=json.dumps(payload).encode("utf-8"), headers=self.builder.headers, method="POST")` | `builder.headers` already includes `Content-Type: application/json` per-backend, so no extra header setup needed |
| `http.use_ssl = uri.scheme == "https"` / `verify_mode = VERIFY_PEER` / commented-out `ca_file` workaround | plain `urllib.request.urlopen(request)` | `urlopen` auto-selects `ssl.create_default_context()` for `https://` URLs and finds system certs on every platform — no Ruby-style workaround needed (see Decisions) |
| `RETRYABLE_STATUS_CODES = [408, 409, 429, 500, 502, 503, 504].freeze` | `RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}` | class attribute, same values |
| `TRANSIENT_ERRORS = [EOFError, Errno::ECONNRESET, Errno::ECONNREFUSED, Net::OpenTimeout, Net::ReadTimeout, OpenSSL::SSL::SSLError, SocketError, Timeout::Error]` | `TRANSIENT_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionResetError, ConnectionRefusedError, ssl.SSLError, http.client.HTTPException, EOFError)` | not a 1:1 class mapping — Python's `URLError` already wraps most connection/timeout/DNS failures; see Decisions |
| `MAX_RETRIES = 3` / `BASE_RETRY_DELAY = 0.5` | same names, same values, class attributes | |
| `call(max_output_tokens: 1024)` retry loop (`loop do ... end`, `attempts += 1`, rescue transient errors, check `retryable_response?`, `break` on success/exhaustion) | `call(self, max_output_tokens=1024)` using a `while True:` loop with the same attempt-counting and branching | Ruby's success path checks `response.is_a?(Net::HTTPSuccess)` *after* the loop; Python's `urlopen` raises `urllib.error.HTTPError` immediately for non-2xx, so the retryable-status check and the final `raise ApiError` both move into an `except urllib.error.HTTPError as e:` branch (`e.code`, `e.read()`) instead of an after-the-loop status check — same observable behavior (retry retryable codes, raise `ApiError` with code+body otherwise), different control flow shape because of how each language's HTTP client surfaces non-2xx responses |
| `rescue *TRANSIENT_ERRORS => e ... raise ApiError if attempts > MAX_RETRIES ... sleep retry_delay(attempts)` | `except TRANSIENT_ERRORS as e:` with the same attempts-exceeded check and `time.sleep(self._retry_delay(attempts))` | same semantics |
| `retryable_response?(response)` (private) | not a separate method — inlined as `e.code in self.RETRYABLE_STATUS_CODES` inside the `HTTPError` branch (see row above) | simplification following from the control-flow difference, not a behavior change |
| `retry_delay(attempt)` (private) | `_retry_delay(self, attempt)` | `self.BASE_RETRY_DELAY * (2 ** (attempt - 1))`, identical formula |
| `JSON.parse(response.body)` | `json.loads(response.read())` | on the success path, inside the `with urllib.request.urlopen(request) as response:` block |
| `raise ApiError, "API request failed after #{attempts} attempt#{'s' unless attempts == 1} (#{response.code}): #{response.body}"` | `raise ApiError(f"API request failed after {attempts} attempt{'s' if attempts != 1 else ''} ({e.code}): {e.read().decode('utf-8', errors='replace')}") from e` | same message format, pluralization included |
| `Tasks::Base.fetch(settings, key)` — Ruby's `04_api_client` adds `return nil unless settings.is_a?(Hash)` | Python's `_fetch(settings, key)` in `tasks/base.py` gets the same guard: `if not isinstance(settings, dict): return None` before `settings.get(str(key))` | defensive fix carried from Ruby — without it, a non-dict `settings` (e.g. `None` for a missing task) would raise `AttributeError` instead of returning `None` |
| `tasks.#{task_name}.provider is required in settings.yml` / `...model is required in settings.yml` wording | no change needed | Python's `tasks/base.py` already says `settings.yaml` (not `.yml`) since `00_config` — Ruby's `04_api_client` just catches up to wording Python already had |
| `config.rb`'s comment change (`"gem/library"` → `"this step"`) | no change needed | comment-only in Ruby; Python's `config.py` already has its own wording (`"Default prompts shipped alongside this package."`) that doesn't reference gems — nothing to port |
| `lib/boukensha.rb` require list drops `backends/base` (still pulled in transitively by each backend file) and adds `client` | `boukensha/__init__.py` adds `Client` to the existing re-exports | no transitive-require concept in Python either way — `backends/__init__.py` already handles its own imports |
| `prompts/system.md` content | copy Ruby's new text verbatim: *"You are Boukensha, an autonomous player exploring a CircleMUD world. Use available tools to observe the world, act deliberately, and explain only what matters for the current turn."* | replaces `03_prompt_builder`'s MUD-player-assistant text — this is real content, not carryover |
| `example.rb`'s `look`/`move` tools, MUD-arrival message | `example.py` registers `read_file(path)` (returns `File.read(path)` → `Path(path).read_text()`) and `list_directory(path)` (`Dir.entries(path).reject { starts_with "." }.join("\n")` → `"\n".join(sorted(p.name for p in Path(path).iterdir() if not p.name.startswith(".")))`) | Ruby's `Dir.entries` order is filesystem-dependent and unspecified; sorting in Python is a reasonable deterministic choice — note this as an intentional minor divergence in the README, not a bug |
| `ctx.add_message(:user, "What files are in the current directory?")` | same string, `ctx.add_message("user", ...)` | |
| `client = Boukensha::Client.new(builder)` / `response = client.call` | `client = Client(builder)` / `response = client.call()` | |
| `puts "=== BOUKENSHA Step 4: API Client ==="` ... `puts "Sending request to #{builder.url}..."` ... `JSON.pretty_generate(response)` | same labeled `print(...)` lines, `json.dumps(response, indent=2)` | same order: header, blank, Config, Provider, Model, "Sending request to {url}...", blank, "Raw response:", pretty JSON |

## Config directory resolution (unchanged)

Same as `03_prompt_builder`: `BOUKENSHA_DIR` env var, else `~/.boukensha`,
resolved via `pathlib`. `PROMPTS_DIR` resolution unchanged. No changes in
this step beyond the new `prompts/system.md` content itself.

## Config schema (unchanged)

No new `settings.yaml` keys. Same `tasks.player.{provider,model,prompt_override}`
shape as every prior step. The repo's existing `.boukensha/settings.yaml`
(`provider: anthropic`, `model: claude-haiku-4-5`) is what the verified
output below was captured against.

## Verified Ruby output (source of truth for shape, not exact text — see Decisions)

Captured by running `./week1_baseline/bin/ruby/04_api_client` for real
against the repo's `.boukensha/` directory and a live Anthropic API key:

```
=== BOUKENSHA Step 4: API Client ===

Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Sending request to https://api.anthropic.com/v1/messages...

Raw response:
{
  "model": "claude-haiku-4-5-20251001",
  "id": "msg_011CdnjWFipqmKikYBeAjhc4",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll list the files in the current directory for you."
    },
    {
      "type": "tool_use",
      "id": "toolu_01Ma631pBExgkg3uYzpoSpQS",
      "name": "list_directory",
      "input": {
        "path": "."
      },
      "caller": {
        "type": "direct"
      }
    }
  ],
  "stop_reason": "tool_use",
  "stop_sequence": null,
  "stop_details": null,
  "usage": {
    "input_tokens": 691,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation": {
      "ephemeral_5m_input_tokens": 0,
      "ephemeral_1h_input_tokens": 0
    },
    "output_tokens": 65,
    "service_tier": "standard",
    "inference_geo": "not_available"
  }
}
```

The Python port's own live run will almost certainly return different
`text`/`id`/`usage` values (and could return `stop_reason: "end_turn"`
instead of `"tool_use"` depending on what the model decides) — verification
means matching the **labeled lines and JSON field structure** (same top-level
keys, same `content` block shapes for `text`/`tool_use`, same `usage`
sub-fields), not matching this exact payload byte-for-byte.

## Implementation steps

1. **Scaffold** `week1_baseline/python/04_api_client/` per the layout above;
   copy `requirements.txt` from `03_prompt_builder` unchanged.
2. **`boukensha/tool.py`, `boukensha/message.py`, `boukensha/context.py`,
   `boukensha/config.py`, `boukensha/registry.py`, `boukensha/prompt_builder.py`,
   `boukensha/tasks/player.py`, `boukensha/backends/*.py`** — copy unchanged
   from `03_prompt_builder`.
3. **`boukensha/tasks/base.py`** — copy from `03_prompt_builder`, add the
   `isinstance(settings, dict)` guard to `_fetch` per the mapping table.
4. **`boukensha/errors.py`** — add `class ApiError(Exception): pass`
   alongside the existing `UnknownToolError`, `UnsupportedModelError`.
5. **`prompts/system.md`** — new content, copied verbatim from Ruby's
   `04_api_client/prompts/system.md` (see mapping table for the text).
6. **`boukensha/client.py`** — `Client` class per the mapping table:
   `RETRYABLE_STATUS_CODES`, `TRANSIENT_ERRORS`, `MAX_RETRIES`,
   `BASE_RETRY_DELAY` class attributes; `__init__(self, builder)`;
   `call(self, max_output_tokens=1024)` building the request via
   `urllib.request.Request`, looping with attempt-counting, catching
   `urllib.error.HTTPError` (retry on retryable codes, else raise
   `ApiError`) and `TRANSIENT_ERRORS` (retry until `MAX_RETRIES` exhausted,
   else raise `ApiError`); `_retry_delay(self, attempt)` helper.
7. **`boukensha/__init__.py`** — add `Client` to the existing re-exports
   from `03_prompt_builder`.
8. **`examples/example.py`** — port `example.rb` line-for-line per the
   mapping table: same `BOUKENSHA_DIR` fallback, register `read_file` and
   `list_directory` tools through the registry, add the single user message,
   resolve `provider`/`model` from `Player`, branch to construct the
   matching backend (same 5-provider branch as `03_prompt_builder`'s
   example), build `PromptBuilder` and `Client`, print the labeled lines in
   order, call `client.call()`, print `json.dumps(response, indent=2)`.
9. **`week1_baseline/bin/python/04_api_client`** — new bash script, same
   template as every prior step's entry script:
   ```bash
   #!/usr/bin/env bash

   cd "$(dirname "$0")/../../python/04_api_client"
   source .venv/bin/activate
   python examples/example.py
   ```
   (`chmod +x`).
10. **`README.md`** in `python/04_api_client/` — same shape as the Ruby
    README (New Files, How It Works diagram, `Client` method table, Task
    Configuration, "No Dependencies" section reframed for `urllib` instead
    of `net/http`, "What the Response Looks Like" examples, Considerations,
    Run Example) — but with the New/Updated Files tables reflecting the
    *actual* diff-verified changes (per the stale-README Decision above,
    not copied from Ruby's tables), and the Output Example using this
    port's own live run rather than Ruby's captured text.
11. **Verify**: run `./week1_baseline/bin/python/04_api_client` for real and
    confirm the printed structure matches the shape documented in "Verified
    Ruby output" above (labeled lines, JSON top-level keys, `content`/`usage`
    field shapes) — not exact text, per the Decisions section. Also smoke-test
    the retry path is at least reachable (e.g. temporarily pointing at an
    invalid host and confirming an `ApiError` is eventually raised with a
    reasonable message), since the happy path alone doesn't exercise it.

## Out of scope for this step

- No tool-call loop / no actually executing `read_file`/`list_directory`
  when the model requests them — that's step 5 (the Agent Loop) per the
  Ruby README's own scope note ("Handling those differences is the job of
  step 5").
- No new config keys or schema changes.
- No `pyproject.toml`/packaging, no CLI entry-point registration, no test
  suite, no `requests`/`httpx` dependency — per the HTTP-library Decision
  above and precedent from every prior step.
- No fixes to rough edges already carried over from `00_config`/
  `01_struct_skeleton`/`02_the_registry`/`03_prompt_builder` (`.yml`
  extension question, missing-settings-file handling, `Context`/`Registry`'s
  dual ownership of tools).
- The Ruby README's own "Review Considerations" flags two known rough edges
  in the Ruby code itself (Ollama's hardcoded local address instead of an
  env var; `Client` not being fully stateless like other classes) — these
  are Ruby-side acknowledged trade-offs, not bugs to fix during the port;
  the Python `Client` carries the same non-stateless shape (holds `builder`
  as instance state) to match.
