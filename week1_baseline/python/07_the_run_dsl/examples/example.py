import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import boukensha  # noqa: E402

# Config is loaded automatically inside boukensha.run() -- system prompt,
# model, and API key all come from ~/.boukensha (or BOUKENSHA_DIR) by
# default. You can still override any of them as keyword arguments if you
# want.

os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))

base_dir = Path(__file__).resolve().parent.parent


def _read_file(path):
    return Path(base_dir, path).resolve().read_text()


def _list_directory(path):
    entries = sorted(p.name for p in Path(base_dir, path).resolve().iterdir() if not p.name.startswith("."))
    return ", ".join(entries)


def _configure(dsl):
    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={"path": {"type": "string", "description": "The file path to read"}},
        block=_read_file,
    )

    dsl.tool(
        "list_directory",
        description="List the files in a directory",
        parameters={"path": {"type": "string", "description": "The directory path to list"}},
        block=_list_directory,
    )


print("=== BOUKENSHA Step 7: The boukensha.run DSL ===")
print()
print(f"Config: {boukensha.get_config()}")
print()

result = boukensha.run(
    task="Read the README.md file and summarise what this MUD player assistant framework can do.",
    configure=_configure,
)

print()
print("=== FINAL RESPONSE ===")
print(result)
