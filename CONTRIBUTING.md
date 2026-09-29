# Contributing

Small, reproducible reports and focused pull requests are welcome. Describe the
expected path resolution and include a minimal synthetic skill tree. Do not upload
private instructions or credentials. Follow the [code of conduct](CODE_OF_CONDUCT.md).

## Setup

Use Python 3.11+ in a virtual environment:

```bash
python -m pip install -e '.[dev]'
python -m pytest --cov=skillspine --cov-report=term-missing
ruff check .
ruff format --check .
mypy src
python -m build
pip-audit
```

Tests exercise temporary real filesystem trees, graph traversal and CLI contracts.
Add a regression test when changing path resolution, parsing, or exit behavior.
Keep source-derived data out of HTML/JS code; render escaped strings only.

## Structure

- `inventory.py`: bounds and filesystem access.
- `markdown.py`: reference extraction; no interpretation of instructions.
- `engine.py`: graph resolution, reachability and impact.
- `models.py`: versioned public report structure.
- `report.py`, `static/`: text and offline browser report.
- `cli.py`: arguments, explicit TOML, output and exit codes.

New features must have clear static semantics. Avoid model calls, telemetry,
implicit configuration discovery, and executing files from a collection. A report
schema breaking change needs a version bump and migration notes.

## Optional browser verification

The development-only browser test is separate from Python dependencies:

```bash
cd tests/browser
npm ci
npx playwright install chromium
npm test
```

This generates a report into a temporary directory, checks filtering, layout
switching, export and mobile sizing, and rejects script errors or HTTP requests.
To use installed Chrome instead, set `SKILLSPINE_BROWSER_CHANNEL=chrome`.

## Pull requests

Explain the concrete behavior change and tests run. Keep unrelated formatting or
refactoring out of the change. All contributions are under the project's MIT license.
