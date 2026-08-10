import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import boukensha  # noqa: E402

# Config is loaded automatically inside boukensha.repl() -- system prompt,
# model, and API key all come from ~/.boukensha (or BOUKENSHA_DIR) by
# default.

os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))

# The base directory tools will operate relative to — the step 7 folder
# makes a good playground since it already has source files to read.
base_dir = Path(__file__).resolve().parents[2] / "07_the_run_dsl"


def _read_file(path):
    return Path(base_dir, path).resolve().read_text()


def _list_directory(path):
    entries = sorted(p.name for p in Path(base_dir, path).resolve().iterdir() if not p.name.startswith("."))
    return ", ".join(entries)


def _configure(dsl):
    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={"path": {"type": "string", "description": "File path (relative to the working directory)"}},
        block=_read_file,
    )

    dsl.tool(
        "list_directory",
        description="List the files in a directory",
        parameters={"path": {"type": "string", "description": "Directory path (relative to the working directory, or '.' for root)"}},
        block=_list_directory,
    )


print(f"Config: {boukensha.get_config()}")
print()

boukensha.repl(configure=_configure)
