# The API Client (Python port)

Python port of `week1_baseline/ruby/04_api_client`. Same behavior, same
output shape (aside from the display divergences noted below) — takes the
payload assembled by `PromptBuilder` (ported in `python/03_prompt_builder`)
and sends it to the API. One HTTP POST, one response. No tool loop yet —
just proving the round trip works.

## Setup

```bash
cd week1_baseline/python/04_api_client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## New Files

| File | Description |
|---|---|
| `boukensha/client.py` | Makes the HTTP request and parses the response |

## Updated Files

| File | Change |
|---|---|
| `boukensha/errors.py` | Added `ApiError` for failed HTTP requests |
| `boukensha/tasks/base.py` | `_fetch` now guards against a non-dict `settings` (returns `None` instead of raising) |
| `prompts/system.md` | New default system prompt text ("Boukensha, an autonomous player...") replacing the MUD-flavored text from `03_prompt_builder` |

Everything else (`config.py`, `tool.py`, `message.py`, `context.py`,
`registry.py`, `prompt_builder.py`, `tasks/player.py`, `backends/*.py`) is an
unchanged copy from `03_prompt_builder` — confirmed by diffing the Ruby
sources, this step doesn't touch them.

*(Ruby's own README for this step lists `backends/base.rb`, `tasks/base.rb`,
`tasks/player.rb`, and `prompts/system.md` as "New Files" and claims
`backends/*.rb` "now own supported model tables" — neither is accurate for
this diff; those files and that feature were already in place as of
`03_prompt_builder`. The tables above reflect what actually changed.)*

## How It Works

```
PromptBuilder
      ↓
Client
      ↓
POST to API endpoint
      ↓
Raw JSON response
```

## Client

| Method | Description |
|---|---|
| `call(max_output_tokens=1024)` | POSTs the payload and returns the parsed JSON response |

## Task Configuration

Unchanged from `03_prompt_builder`:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
```

When `prompt_override.system` is true, Boukensha reads
`.boukensha/prompts/player/system.md`. Otherwise it falls back to this
step's shipped `prompts/system.md`.

## No Dependencies

`Client` uses Python's standard `urllib.request` / `urllib.error` /
`http.client` modules. No `requests`, no `httpx`, `requirements.txt` is
unchanged from `03_prompt_builder` (`PyYAML`, `python-dotenv`). This mirrors
the Ruby version's own choice to use `net/http` instead of a gem — the HTTP
call stays visible, not hidden behind a library.

Unlike Ruby's `client.rb`, no SSL certificate workaround is needed here:
Ruby's comment explains it omits `ca_file` because the macOS default path
doesn't exist on Linux/WSL2, relying on OpenSSL to find system certs.
Python's `urllib.request.urlopen` already uses `ssl.create_default_context()`
for `https://` URLs, which finds system CA certs automatically on every
platform, so there's no equivalent quirk to route around.

## What the Response Looks Like

The raw response shape differs between backends. This is what you get back
from `client.call()` before any processing — captured from an actual run of
this port (see Run Example below) rather than reproduced from the Ruby
README:

### Anthropic
```json
{
  "model": "claude-haiku-4-5-20251001",
  "id": "msg_...",
  "type": "message",
  "role": "assistant",
  "content": [
    { "type": "text", "text": "..." }
  ],
  "stop_reason": "end_turn",
  "usage": { "input_tokens": 691, "output_tokens": 65 }
}
```

### Ollama
```json
{
  "model": "llama3.2",
  "message": {
    "role": "assistant",
    "content": "Sure, let me read that file."
  },
  "done_reason": "stop",
  "done": true
}
```

When the model wants to call a tool the response looks different. Anthropic
uses `stop_reason: "tool_use"` and adds a `tool_use` block to `content`.
Ollama adds a `tool_calls` array to `message`. Handling those differences is
the job of step 5 — the Agent Loop.

## Considerations

**The client raises `ApiError` on failure.** A non-2xx response, or a
network-level failure that survives retries, means something went wrong —
bad API key, malformed payload, server error, dropped connection. BOUKENSHA
surfaces this explicitly rather than returning a confusing `None` or partial
response.

**Retries are automatic for transient failures.** Up to 3 retries with
exponential backoff (0.5s, 1s, 2s) for retryable HTTP status codes (`408,
409, 429, 500, 502, 503, 504`) and for transient network errors (connection
reset/refused, timeouts, SSL errors, other URL errors). Anything else fails
immediately.

**SSL is handled automatically.** `urlopen` enables SSL verification for
`https://` endpoints using the system's default CA certificates. Ollama
running locally uses plain `http://` so no SSL is involved.

## Run Example

```bash
./week1_baseline/bin/python/04_api_client
```

Actual output from a live run against this repo's `.boukensha/` (provider
`anthropic`, model `claude-haiku-4-5`) — the response `text`/`id`/`usage`
values are LLM-generated and will differ on every run, including possibly
returning plain text instead of a `tool_use` block:

```
=== BOUKENSHA Step 4: API Client ===

Config: #<Boukensha::Config dir=/home/drew/bootcamps/claude-code-camp-2026-Q2/.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Sending request to https://api.anthropic.com/v1/messages...

Raw response:
{
  "model": "claude-haiku-4-5-20251001",
  "id": "msg_011CdnkHr7J1Jr11hiaXRbxr",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll list the files in the current directory for you."
    },
    {
      "type": "tool_use",
      "id": "toolu_0156q8cKrkoJSSoe2UNv9ZZM",
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

Field-for-field structure matches the Ruby run captured in
[docs/plans/python_port/04_api_client.md](../../../docs/plans/python_port/04_api_client.md).
This is a real, billed call to whichever provider your `.boukensha/settings.yaml`
configures — the other four backends (`Gemini`, `Ollama`, `OllamaCloud`,
`OpenAI`) are ported but not exercised unless you configure the `player`
task to use one of them.

## Ruby → Python idiom differences

- **HTTP client shape.** Ruby's success path checks
  `response.is_a?(Net::HTTPSuccess)` *after* `http.request` returns; Python's
  `urlopen` raises `urllib.error.HTTPError` immediately for any non-2xx
  response, so the retryable-status check and the final `ApiError` both live
  inside an `except urllib.error.HTTPError` branch instead of an
  after-the-fact status check. Same observable behavior, different control
  flow because of how each language's HTTP client surfaces failures.
- **Transient error list isn't a 1:1 class mapping.** Ruby's
  `TRANSIENT_ERRORS` names 8 specific exception classes. Python's
  `urllib.error.URLError` already wraps most connection-refused/timeout/DNS
  failures internally, so the Python tuple
  (`URLError`, `TimeoutError`, `ConnectionResetError`, `ConnectionRefusedError`,
  `ssl.SSLError`, `http.client.HTTPException`, `EOFError`) covers the same
  "retry on transient network failure" intent with fewer, broader classes.
- `Dir.entries` (Ruby, filesystem order, unspecified) becomes
  `sorted(Path(path).iterdir())` in `examples/example.py`'s `list_directory`
  tool — a deterministic ordering choice, not a behavior difference the
  agent would notice.
- `Config`'s `__str__` keeps the `Boukensha::Config` string byte-identical to
  Ruby, same choice made in every prior port in this series.

## Out of scope

- No tool-call loop / no actually executing `read_file`/`list_directory`
  when the model requests them — that's step 5 (the Agent Loop), matching
  the Ruby README's own scope note.
- `Context`/`Registry`'s dual ownership of tools, flagged in the
  `02_the_registry` port's README, is still unresolved here — carried
  forward unchanged.
- Ollama's backend still hardcodes `http://localhost:11434` rather than
  reading an env var — a known rough edge acknowledged in Ruby's own
  "Review Considerations" section, carried forward unchanged rather than
  fixed as a drive-by.
- `Client` holds `builder` as instance state rather than being fully
  stateless like the other classes — also acknowledged as a known trade-off
  in Ruby's "Review Considerations", carried forward unchanged to match.
