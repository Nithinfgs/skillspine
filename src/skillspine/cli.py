"""CLI orchestration and strict, explicit TOML configuration."""

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from . import __version__
from .engine import scan
from .models import ScanError
from .report import html_report, text_report


def _config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
    except (OSError, ValueError) as exc:
        raise ScanError("Cannot read configuration as TOML.") from exc
    known = {"exclude", "code_paths", "max_files", "max_markdown_bytes"}
    if set(data) - known:
        raise ScanError("Unknown configuration key(s): " + ", ".join(sorted(set(data) - known)))
    if "exclude" in data and (
        not isinstance(data["exclude"], list)
        or any(not isinstance(p, str) or not p for p in data["exclude"])
    ):
        raise ScanError("exclude must be an array of nonempty strings.")
    if "code_paths" in data and not isinstance(data["code_paths"], bool):
        raise ScanError("code_paths must be true or false.")
    for key in ("max_files", "max_markdown_bytes"):
        if key in data and (type(data[key]) is not int or not 1 <= data[key] <= 100_000_000):
            raise ScanError(f"{key} must be a positive integer no larger than 100000000.")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Map agent skill dependencies, change impact, and isolated-install failures."
    )
    parser.add_argument("--version", action="version", version=f"skillspine {__version__}")
    parser.add_argument("root", type=Path, help="skill folder or collection root")
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        metavar="PATH",
        help="changed file relative to root; repeat for multiple files",
    )
    parser.add_argument("--layout", choices=("collection", "isolated"), default="isolated")
    parser.add_argument("--format", choices=("text", "json", "html"), default="text")
    parser.add_argument("--output", type=Path, help="write a new report file; refuses overwrite")
    parser.add_argument(
        "--config", type=Path, help="explicit TOML configuration (never auto-loaded)"
    )
    parser.add_argument(
        "--code-paths",
        action="store_true",
        default=None,
        help="also infer references from path-like inline code spans",
    )
    parser.add_argument("--exclude", action="append", default=[], help="exclude glob; repeatable")
    parser.add_argument(
        "--fail-on",
        choices=("findings", "impact", "never"),
        default="findings",
        help="exit 1 on layout findings (default), affected skills, or never",
    )
    args = parser.parse_args(argv)
    try:
        config = _config(args.config)
        report = scan(
            args.root,
            changed=args.changed,
            code_paths=args.code_paths
            if args.code_paths is not None
            else config.get("code_paths", False),
            exclude=tuple(config.get("exclude", []) + args.exclude),
            max_files=config.get("max_files", 20000),
            max_markdown_bytes=config.get("max_markdown_bytes", 1_000_000),
        )
        if args.format == "json":
            output = json.dumps(report.to_dict(), indent=2, ensure_ascii=True)
        elif args.format == "html":
            output = html_report(report, args.layout)
        else:
            output = text_report(report, args.layout)
        if args.output:
            # Exclusive create avoids destroying source files or following output symlinks.
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(output + "\n")
        else:
            print(output)
        if args.fail_on == "impact":
            return int(any(s.impacts for s in report.skills))
        if args.fail_on == "findings":
            return int(any(getattr(s, args.layout) for s in report.skills))
        return 0
    except (ScanError, OSError, RecursionError) as exc:
        if isinstance(exc, ScanError):
            message = str(exc)
        elif isinstance(exc, FileExistsError):
            message = "Output already exists; choose a new path or remove the old report."
        else:
            message = "Scan or output failed (filesystem, permissions, or parser depth limit)."
        print(f"skillspine: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
