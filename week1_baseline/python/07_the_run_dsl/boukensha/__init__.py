import os

_quiet = False
_debug = False
_config = None


def set_quiet(value=True):
    global _quiet
    _quiet = value


def set_loud():
    global _quiet
    _quiet = False


def is_quiet():
    return _quiet


def set_debug(value=True):
    global _debug
    _debug = value


def is_debug():
    return _debug


def get_config():
    global _config
    if _config is None:
        _config = Config()
    return _config


from .agent import Agent
from .backends import Anthropic, Gemini, Ollama, OllamaCloud, OpenAI
from .client import Client
from .config import PROMPTS_DIR, Config
from .context import Context
from .errors import ApiError, LoopError, UnknownToolError, UnsupportedModelError
from .logger import Logger
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .run_dsl import RunDSL
from .tasks.player import Player
from .tool import Tool


def run(task, system=None, model=None, backend=None, api_key=None,
        ollama_host="http://localhost:11434", log=None, max_output_tokens=None,
        configure=None):
    """The top-level entry point. Wires together every primitive so the
    caller only has to describe *what* to do, not *how* to plumb it.

        result = boukensha.run(task="Summarise lib/boukensha.rb", configure=lambda dsl: dsl.tool(
            "read_file",
            description="Read a file from disk",
            parameters={"path": {"type": "string", "description": "File path"}},
            block=lambda path: open(path).read(),
        ))

    Options:
      task:         (required) The user message to hand the agent.
      system:       System prompt. Defaults to the player task's system prompt.
      model:        Model name. Defaults to the player task's configured model.
      backend:      "anthropic", "openai", "gemini", "ollama", or "ollama_cloud".
                    Defaults to the player task's configured provider.
      api_key:      API key for the chosen backend. Defaults to the matching
                    ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY / OLLAMA_API_KEY
                    env var (loaded from .boukensha/.env). Not needed for "ollama".
      ollama_host:  Ollama base URL. Defaults to "http://localhost:11434".
      log:          Optional JSONL path override. Defaults to .boukensha/sessions/<session-id>.jsonl.
      max_output_tokens: Per-reply output cap. Defaults to the player task's setting (1024).
      configure:    Optional callable taking a RunDSL instance, for registering tools:
                    configure=lambda dsl: dsl.tool(...)
    """
    cfg = get_config()  # loads .env
    task_class = Player
    task_settings = cfg.tasks(task_class.task_name())
    system = system or task_class.system_prompt(
        task_settings, user_prompts_dir=cfg.user_prompts_dir, default_prompts_dir=PROMPTS_DIR
    )
    model = model or task_class.model(task_settings)
    backend = backend or task_class.provider(task_settings)
    if api_key is None:
        api_key = {
            "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
            "openai": os.environ.get("OPENAI_API_KEY"),
            "gemini": os.environ.get("GEMINI_API_KEY"),
            "ollama_cloud": os.environ.get("OLLAMA_API_KEY"),
        }.get(backend)

    ctx = Context(task=task_class, system=system)
    registry = Registry(ctx)

    if configure is not None:
        configure(RunDSL(registry))

    if backend == "anthropic":
        be = Anthropic(api_key=api_key, model=model)
    elif backend == "openai":
        be = OpenAI(api_key=api_key, model=model)
    elif backend == "gemini":
        be = Gemini(api_key=api_key, model=model)
    elif backend == "ollama":
        be = Ollama(model=model, host=ollama_host)
    elif backend == "ollama_cloud":
        be = OllamaCloud(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'.")

    builder = PromptBuilder(ctx, be)
    client = Client(builder)
    effective_max_iterations = task_class.max_iterations(task_settings)
    effective_max_output_tokens = max_output_tokens or task_class.max_output_tokens(task_settings)
    logger = Logger(log=log, snapshot={
        "task": task_class.task_name(),
        "max_iterations": effective_max_iterations,
        "max_output_tokens": effective_max_output_tokens,
        "model": model,
        "provider": backend,
    })
    agent = Agent(ctx, registry, builder, client, logger=logger,
                   task_settings=task_settings, max_iterations=effective_max_iterations,
                   max_output_tokens=effective_max_output_tokens)

    try:
        ctx.add_message("user", task)
        return agent.run()
    finally:
        logger.close()


__all__ = [
    "Agent",
    "Anthropic",
    "ApiError",
    "Client",
    "Config",
    "Context",
    "Gemini",
    "get_config",
    "is_debug",
    "is_quiet",
    "Logger",
    "LoopError",
    "Message",
    "Ollama",
    "OllamaCloud",
    "OpenAI",
    "Player",
    "PromptBuilder",
    "Registry",
    "run",
    "RunDSL",
    "set_debug",
    "set_loud",
    "set_quiet",
    "Tool",
    "UnknownToolError",
    "UnsupportedModelError",
]
