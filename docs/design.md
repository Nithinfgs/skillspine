# Product and technical design

## Pitch
See which agent skills a shared-file change affects, and which break when installed alone.

## Problem and audience
Maintainers share checklists, scripts and assets across a collection. A change to one
reference can affect many skills indirectly. A reference that works in a checkout
can disappear when an installer copies only one skill directory. This tool serves
skill authors, plugin maintainers and reviewers of shared instruction libraries.

## Differentiator and scope
One dependency graph powers two answers: reverse change impact with explanatory
paths, and full-collection versus isolated-folder install checks. It complements
metadata/content validators. It does not claim to be the first link checker, certify
host compatibility, execute skills, or inspect natural-language intent.

## MVP
- Discover SKILL.md entrypoints recursively, including hidden host directories.
- Parse CommonMark links/images/reference links and optional path-like code spans.
- Follow local Markdown dependencies transitively with cycle-safe traversal.
- Check missing files, exact case, symlinks and collection boundaries.
- Compare collection and isolated skill-folder availability.
- Explain changed-file impact with shortest dependency paths.
- Text, versioned JSON, and standalone interactive HTML reports; deterministic CI exits.
- Read-only, offline scanning; bounded file count and Markdown size.

## Architecture
Python 3.11+, markdown-it-py for CommonMark parsing, standard library everywhere else.
`inventory.py` indexes regular files without following symlinks. `markdown.py` extracts
references without rendering untrusted markup. `engine.py` resolves edges and computes
reachability and impact. `report.py` renders escaped HTML. `cli.py` owns configuration,
input validation and exit codes. Dataclasses form the public report model.

Data flow: root + TOML config → bounded inventory → parsed Markdown graph → per-skill
breadth-first traversal → portability findings + impact paths → text/JSON/HTML.
No database, server, API keys, external link requests, or content execution. Reports
store relative paths and metadata, never file bodies; paths can still be sensitive.

## Semantics
Links resolve relative to the Markdown file containing them. Code spans are optional,
heuristic edges; their separate kind remains visible. Anchors do not affect file
availability and are not validated. Scripts/assets are leaf nodes; imports and shell
commands are not inferred. Directory links are review findings, never an implicit
recursive dependency. All symlinks are rejected, including internal ones, for stable
cross-machine behavior. A single skill root can be `.`. A collection must contain at
least one regular SKILL.md. Remote URLs are counted but never fetched or stored.

## Security and verification
Never follow symlinks, read outside the root, invoke subprocesses, render source HTML,
or execute embedded commands. Bound inventory and per-Markdown byte size. Reject
unsupported config keys. HTML escapes every source-derived value; JS only filters
already-rendered rows. Test real temporary directory graphs, hostile paths and markup,
cycles, CLI exit codes, deterministic outputs, installed wheel, and browser controls.

## Later
Git-aware deleted/renamed dependency impact, installer-specific inclusion manifests,
SARIF, editor integration, and explicit script dependency adapters. None is in v0.1.
