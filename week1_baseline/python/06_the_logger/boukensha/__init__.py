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
from .config import Config
from .context import Context
from .errors import ApiError, UnknownToolError, UnsupportedModelError
from .logger import Logger
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .tasks.player import Player
from .tool import Tool

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
    "Message",
    "Ollama",
    "OllamaCloud",
    "OpenAI",
    "Player",
    "PromptBuilder",
    "Registry",
    "set_debug",
    "set_loud",
    "set_quiet",
    "Tool",
    "UnknownToolError",
    "UnsupportedModelError",
]
