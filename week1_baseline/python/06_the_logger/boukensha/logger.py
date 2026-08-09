import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from . import get_config, is_debug


class Logger:
    DEFAULT_SESSION_DIR = "sessions"

    def __init__(self, session_id=None, dir=None, log=None, snapshot=None):
        snapshot = snapshot if snapshot is not None else {}
        self.session_id = session_id or self._generate_session_id()
        self.path = Path(log) if log else Path(dir or self._default_dir()) / f"{self.session_id}.jsonl"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._log_io = open(self.path, "a")
        self._write_log({"phase": "session_start", **snapshot})

    def iteration(self, n, max):
        self._write_log({"phase": "iteration", "n": n, "max": max})

    def limit_reached(self, kind, n, max):
        self._write_log({"phase": "limit_reached", "kind": kind, "n": n, "max": max})

    def turn_end(self, reason, iterations, tokens=None):
        self._write_log({"phase": "turn_end", "reason": reason, "iterations": iterations, "tokens": tokens})

    def prompt(self, messages, tools):
        self._write_log({
            "phase": "prompt",
            "message_count": len(messages),
            "messages": [self._serialize_message(m) for m in messages],
            "tool_count": len(tools),
            "tools": list(tools.keys()),
        })

    def tool_call(self, name, args):
        self._write_log({"phase": "tool_call", "name": name, "args": args})

    def tool_result(self, name, result, ok=True, error=None):
        self._write_log({"phase": "tool_result", "name": name, "result": str(result), "ok": ok, "error": error})

    def response(self, text, usage=None, stop_reason=None, task=None, backend=None):
        event = {
            "phase": "response",
            "text": str(text).strip(),
            "usage": usage,
            "stop_reason": stop_reason,
        }
        event.update(self._execution_metadata(task, backend, usage))
        self._write_log(event)

    def raw(self, data):
        if not is_debug():
            return

        self._write_log({"phase": "raw", "data": data})

    def close(self):
        self._log_io.close()

    # ---------- private ---------------------------------------------------

    def _default_dir(self):
        return str(Path(get_config().dir) / self.DEFAULT_SESSION_DIR)

    def _write_log(self, event):
        self._log_io.write(json.dumps({**event, "session_id": self.session_id, "at": self._now_iso()}) + "\n")
        self._log_io.flush()

    def _now_iso(self):
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _generate_session_id(self):
        return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"

    def _serialize_message(self, msg):
        return {"role": msg.role, "content": msg.content}

    def _execution_metadata(self, task, backend, usage):
        if not (task or backend or usage):
            return {}

        tokens = self._usage_tokens(usage)
        metadata = {
            "task": self._task_name(task),
            "provider": self._provider_name(backend),
            "model": backend.model if backend else None,
            "usage_unit": backend.usage_unit if backend else None,
            "usage_level": backend.usage_level if backend else None,
            "input_tokens": tokens["input"],
            "output_tokens": tokens["output"],
            "cost_usd": self._estimate_cost(backend, tokens),
        }
        return {k: v for k, v in metadata.items() if v is not None}

    def _task_name(self, task):
        if not task:
            return None
        return task.task_name() if hasattr(task, "task_name") else str(task)

    def _provider_name(self, backend):
        if backend is None:
            return None

        return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", type(backend).__name__).lower()

    def _usage_tokens(self, usage):
        usage = usage or {}
        return {
            "input": self._first_integer(usage, "input_tokens", "prompt_tokens", "promptTokenCount", "prompt_eval_count"),
            "output": self._first_integer(usage, "output_tokens", "completion_tokens", "candidatesTokenCount", "eval_count"),
        }

    def _first_integer(self, usage, *keys):
        for key in keys:
            value = usage.get(key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return None
        return None

    def _estimate_cost(self, backend, tokens):
        if backend is None or tokens["input"] is None or tokens["output"] is None:
            return None

        return backend.estimate_cost(tokens["input"], tokens["output"])
