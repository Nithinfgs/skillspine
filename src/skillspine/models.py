"""Versioned report types; all paths use collection-relative POSIX spelling."""

from dataclasses import asdict, dataclass, field
from typing import Any


class ScanError(Exception):
    """Invalid input or incomplete scan; never report an incomplete scan as clean."""


@dataclass(frozen=True)
class Reference:
    target: str
    line: int
    kind: str


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    line: int
    kind: str
    status: str = "ok"


@dataclass(frozen=True)
class Finding:
    code: str
    source: str
    target: str
    line: int
    message: str
    chain: list[str]


@dataclass
class Skill:
    entry: str
    dependencies: list[str] = field(default_factory=list)
    collection: list[Finding] = field(default_factory=list)
    isolated: list[Finding] = field(default_factory=list)
    impacts: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Report:
    skills: list[Skill]
    edges: list[Edge]
    files: int
    external_links: int
    changed: list[str]
    code_paths: bool
    schema_version: int = 1
    tool_version: str = "0.1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
