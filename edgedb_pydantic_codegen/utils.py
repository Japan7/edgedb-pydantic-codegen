import os
import re
import subprocess
from pathlib import Path

from ruff.__main__ import find_ruff_bin


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def camel_to_snake(camel_str: str) -> str:
    return re.sub("([A-Z])", "_\\1", camel_str).lower().lstrip("_")


def ruff_fix(path: Path):
    ruff = find_ruff_bin()
    proc = subprocess.run(
        [
            os.fsdecode(ruff),
            "check",
            "--extend-select",
            "I",
            "--fix-only",
            path.absolute(),
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "Ruff failed to fix the generated code",
            proc.stdout.decode(),
            proc.stderr.decode(),
        )


def ruff_format(path: Path):
    ruff = find_ruff_bin()
    proc = subprocess.run(
        [os.fsdecode(ruff), "format", path.absolute()],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "Ruff failed to format the generated code",
            proc.stdout.decode(),
            proc.stderr.decode(),
        )
