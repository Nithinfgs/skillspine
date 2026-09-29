"""Resolve local reference graphs and explain forward/reverse reachability."""

import posixpath
import re
from collections import deque
from pathlib import Path, PurePosixPath

from .inventory import DEFAULT_EXCLUDES, Inventory, inventory, read_markdown
from .markdown import references
from .models import Edge, Finding, Report, ScanError, Skill

MESSAGES = {
    "missing": "File is missing. Add it or correct the reference.",
    "case_mismatch": "Path spelling differs in case; use the exact filename for Linux installs.",
    "outside_collection": "Reference escapes the collection; move the dependency inside it.",
    "symlink": "Symlinks are not followed. Ship a regular file for portable installation.",
    "directory": "Directory reference has no explicit file dependency; link to a file.",
    "nonportable_path": "Use a relative path with forward slashes, without control characters.",
    "excluded": "Target is excluded from the inventory; adjust the reference or exclusions.",
    "outside_skill": (
        "Dependency is outside this skill folder and will be absent in an isolated copy."
    ),
}


def _under(path: str, parent: str) -> bool:
    return parent == "." or path == parent or path.startswith(parent + "/")


def _resolve(inv: Inventory, source: str, raw: str) -> tuple[str, str]:
    if (
        raw.startswith(("/", "~"))
        or "\\" in raw
        or re.match(r"^[A-Za-z]:", raw)
        or any(ord(c) < 32 or ord(c) == 127 for c in raw)
    ):
        return raw, "nonportable_path"
    target = posixpath.normpath(posixpath.join(posixpath.dirname(source), raw))
    if target == ".." or target.startswith("../"):
        return target, "outside_collection"
    if any(_under(target, p) for p in inv.symlinks):
        return target, "symlink"
    if any(_under(target, p) for p in inv.excluded):
        return target, "excluded"
    if target in inv.files:
        return target, "ok"
    if target in inv.directories:
        return target, "directory"
    candidates = inv.files | inv.directories | inv.symlinks | inv.excluded
    if any(p.casefold() == target.casefold() for p in candidates):
        return target, "case_mismatch"
    return target, "missing"


def normalize_changed(paths: list[str]) -> list[str]:
    result = set()
    for path in paths:
        if (
            not path
            or "\\" in path
            or path.startswith(("/", "~"))
            or re.match(r"^[A-Za-z]:", path)
            or any(ord(c) < 32 for c in path)
        ):
            raise ScanError("Changed paths must be collection-relative paths with forward slashes.")
        path = posixpath.normpath(path)
        if path in {".", ".."} or path.startswith("../"):
            raise ScanError("Changed paths must identify files inside the collection.")
        result.add(path)
    return sorted(result)


def scan(
    root: Path,
    *,
    changed: list[str] | None = None,
    code_paths: bool = False,
    exclude: tuple[str, ...] = (),
    max_files: int = 20000,
    max_markdown_bytes: int = 1_000_000,
) -> Report:
    if max_files < 1 or max_markdown_bytes < 1:
        raise ScanError("Scan limits must be positive.")
    changed_paths = normalize_changed(changed or [])
    inv = inventory(root, DEFAULT_EXCLUDES + exclude, max_files)
    entries = sorted(p for p in inv.files if PurePosixPath(p).name == "SKILL.md")
    if not entries:
        raise ScanError("No regular SKILL.md found. Choose a skill or collection directory.")
    adjacency: dict[str, list[Edge]] = {}
    pending = deque(entries)
    external_count = 0
    while pending:
        source = pending.popleft()
        if source in adjacency:
            continue
        adjacency[source] = []
        if PurePosixPath(source).suffix.lower() != ".md":
            continue
        refs, external = references(read_markdown(inv, source, max_markdown_bytes), code_paths)
        external_count += external
        for ref in refs:
            target, status = _resolve(inv, source, ref.target)
            edge = Edge(source, target, ref.line, ref.kind, status)
            if edge in adjacency[source]:
                continue
            adjacency[source].append(edge)
            if status == "ok" and target not in adjacency:
                pending.append(target)
        adjacency[source].sort(key=lambda e: (e.target, e.line, e.kind))
    skills = []
    for entry in entries:
        skill = Skill(entry)
        folder = posixpath.dirname(entry) or "."
        chains = {entry: [entry]}
        queue = deque([entry])
        dependencies: set[str] = set()
        while queue:
            source = queue.popleft()
            for edge in adjacency.get(source, []):
                chain = chains[source] + [edge.target]
                if edge.status != "ok":
                    finding = Finding(
                        edge.status, source, edge.target, edge.line, MESSAGES[edge.status], chain
                    )
                    skill.collection.append(finding)
                    skill.isolated.append(finding)
                elif not _under(edge.target, folder):
                    skill.isolated.append(
                        Finding(
                            "outside_skill",
                            source,
                            edge.target,
                            edge.line,
                            MESSAGES["outside_skill"],
                            chain,
                        )
                    )
                dependencies.add(edge.target)
                # Unresolved targets still participate in impact (e.g. a deleted file).
                if edge.target not in chains:
                    chains[edge.target] = chain
                    if edge.status == "ok":
                        queue.append(edge.target)
        skill.dependencies = sorted(dependencies - {entry})
        skill.impacts = {p: chains[p] for p in changed_paths if p in chains}
        skills.append(skill)
    return Report(
        skills,
        sorted(
            (e for es in adjacency.values() for e in es),
            key=lambda e: (e.source, e.target, e.line, e.kind),
        ),
        len(inv.files),
        external_count,
        changed_paths,
        code_paths,
    )
