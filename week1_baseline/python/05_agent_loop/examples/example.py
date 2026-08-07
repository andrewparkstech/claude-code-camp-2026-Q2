import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boukensha import (  # noqa: E402
    Agent,
    Anthropic,
    Client,
    Config,
    Context,
    Gemini,
    Ollama,
    OllamaCloud,
    OpenAI,
    Player,
    PromptBuilder,
    Registry,
)
from boukensha.config import PROMPTS_DIR  # noqa: E402

# Override the config directory so the example works from the repo root.
# In real usage a user's ~/.boukensha is picked up automatically.
os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))

config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=PROMPTS_DIR,
)
base_dir = Path(__file__).resolve().parent.parent

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

provider = Player.provider(player_settings)
model = Player.model(player_settings)

if provider == "anthropic":
    backend = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model=model)
elif provider == "openai":
    backend = OpenAI(api_key=os.environ["OPENAI_API_KEY"], model=model)
elif provider == "gemini":
    backend = Gemini(api_key=os.environ["GEMINI_API_KEY"], model=model)
elif provider == "ollama":
    backend = Ollama(model=model)
elif provider == "ollama_cloud":
    backend = OllamaCloud(api_key=os.environ["OLLAMA_API_KEY"], model=model)
else:
    raise ValueError(f"Unsupported provider for player task: {provider}")

builder = PromptBuilder(ctx, backend)
client = Client(builder)
agent = Agent(
    ctx,
    registry,
    builder,
    client,
    task_settings=player_settings,
)


def _read_file(path):
    return Path(base_dir, path).resolve().read_text()


def _list_directory(path):
    entries = sorted(p.name for p in Path(base_dir, path).resolve().iterdir() if not p.name.startswith("."))
    return ", ".join(entries)


registry.tool(
    "read_file",
    description="Read the contents of a file from disk",
    parameters={"path": {"type": "string", "description": "The file path to read"}},
    block=_read_file,
)

registry.tool(
    "list_directory",
    description="List the files in a directory",
    parameters={"path": {"type": "string", "description": "The directory path to list"}},
    block=_list_directory,
)

ctx.add_message(
    "user", "Read the README.md file and summarise what this MUD player assistant framework can do."
)

print("=== BOUKENSHA Step 5: Agent Loop ===")
print()
print(f"Config: {config}")
print(f"Provider: {provider}")
print(f"Model: {model}")
print(f"Max iterations: {Player.max_iterations(player_settings)}")
print(f"Max output tokens: {Player.max_output_tokens(player_settings)}")
print()

result = agent.run()

print()
print("=== FINAL RESPONSE ===")
print(result)
