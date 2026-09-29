"""Bounded filesystem inventory. Never recurse into a symbolic link."""

import fnmatch
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .models import ScanError

DEFAULT_EXCLUDES = (
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".env",
    ".env.*",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
)


@dataclass
class Inventory:
    root: Path
    files: set[str]
    directories: set[str]
    symlinks: set[str]
    excluded: set[str]


def inventory(root: Path, excludes: tuple[str, ...], max_files: int) -> Inventory:
    root = root.resolve()
    if not root.is_dir():
        raise ScanError("Collection root must be an existing directory.")
    result = Inventory(root, set(), {"."}, set(), set())
    pending = [root]
    count = 0
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    rel = (directory / entry.name).relative_to(root).as_posix()
                    count += 1
                    if count > max_files:
                        raise ScanError(
                            f"Inventory exceeds max_files={max_files}; narrow the root."
                        )
                    if any(
                        fnmatch.fnmatchcase(rel, p) or fnmatch.fnmatchcase(entry.name, p)
                        for p in excludes
                    ):
                        result.excluded.add(rel)
                    elif entry.is_symlink():
                        result.symlinks.add(rel)
                    elif entry.is_dir(follow_symlinks=False):
                        result.directories.add(rel)
                        pending.append(directory / entry.name)
                    elif entry.is_file(follow_symlinks=False):
                        result.files.add(rel)
                    else:
                        result.excluded.add(rel)
        except OSError as exc:
            raise ScanError(
                "Cannot inventory collection (permission or filesystem error)."
            ) from exc
    return result


def read_markdown(inv: Inventory, rel: str, limit: int) -> str:
    path = inv.root / rel
    try:
        # Recheck containment and symlink components after inventory. Concurrent writes
        # are not an atomic snapshot; callers should scan a stable checkout.
        if not path.resolve().is_relative_to(inv.root):
            raise ScanError(f"Path escaped the collection while scanning: {rel}")
        cursor = inv.root
        for part in Path(rel).parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise ScanError(f"Path became a symlink while scanning: {rel}")
        fd = os.open(
            path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        )
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ScanError(f"Not a regular file: {rel}")
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ScanError(f"Markdown exceeds max_markdown_bytes={limit}: {rel}")
        return data.decode("utf-8-sig")
    except (OSError, UnicodeError, ValueError) as exc:
        raise ScanError(f"Cannot read UTF-8 Markdown: {rel}") from exc
