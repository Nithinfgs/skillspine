# CLI and report reference

## Boundaries

The root is the collection boundary. Every regular `SKILL.md` under it is an
entrypoint, including skills in hidden directories such as `.agents/skills`.
The entrypoint's parent is its isolated-install boundary. Files elsewhere within
the root may work in collection mode but fail isolated mode.

Traversal follows valid regular-file edges. Invalid edges remain in the graph for
diagnostics and change impact, but their targets are never read. Cycles terminate.
Non-Markdown files are leaves. All valid references are evaluated, not just one path;
impact displays one deterministic shortest path per changed file and skill.

Impact is evaluated against the **current** reference graph. It can find a deleted
file if a reference to it remains. It cannot recover a reference that was itself
removed, detect renames, or compare historical graph versions in v0.1.

## Findings

| Code | Meaning |
|---|---|
| `missing` | No target with that path exists in the inventory |
| `case_mismatch` | A path matches after case folding, but its exact spelling differs |
| `outside_collection` | A normalized relative reference traverses above the supplied root |
| `outside_skill` | Regular dependency exists in collection but lies outside the entrypoint folder |
| `symlink` | Target or one of its ancestor paths is a symbolic link; never followed |
| `directory` | Reference points to a directory; file-level dependency cannot be established |
| `nonportable_path` | Absolute/home/Windows/backslash/control-character path |
| `excluded` | Target is hidden by an exclusion or is not a regular file/directory |

All findings use the same gate severity. This avoids ungrounded risk scoring.
`outside_skill` only appears in isolated findings. Other findings appear in both.
The isolated view retains transitive findings beyond an unavailable boundary, so
maintainers can see all dependencies they would need to colocate.

## Parsing

CommonMark is parsed by markdown-it-py. Frontmatter between an initial `---` line
and a closing `---` or `...` is skipped, preserving line numbers. Fenced code is not
parsed for dependencies. Images, inline and reference-style links participate.
URLs with a scheme or host are counted and skipped; fragment-only links are ignored.
Queries and fragments are stripped before file resolution. Percent-encoded paths
are decoded. External links are not fetched or stored in reports.

`--code-paths` recognizes inline code beginning `./`, `../`, `references/`, `scripts/`,
or `assets/`. Spans containing template markers/globs are excluded. It is a heuristic:
use ordinary Markdown links for precise dependency declarations. Arbitrary bare
paths and code blocks are intentionally ignored. Every edge identifies its source
kind (`link`, `image`, `code`) in JSON.

## JSON schema version 1

Top-level keys:

- `schema_version`, `tool_version`: consumer compatibility markers.
- `files`: number of regular files inventoried, including files not referenced.
- `external_links`: remote links counted in distinct parsed Markdown files.
- `code_paths`: whether heuristic inference was enabled.
- `changed`: sorted, normalized input change paths.
- `edges`: `source`, `target`, `line`, `kind`, `status` (`ok` or a finding code).
- `skills`: one record for every discovered entrypoint.

Skill records contain `entry`, sorted unique `dependencies`, `collection` and
`isolated` findings, and `impacts` mapping each affected changed path to its
entrypoint-to-file path. Dependencies include unresolved reference targets and
exclude the entrypoint itself. A change to the entrypoint is an impact path of
length one. Finding records include `code`, `source`, `target`, `line`, `message`,
and `chain`.

No timestamps or absolute scan root are included, making repeated scans of a stable
tree reproducible. Source paths embedded in references are reported as written or
normalized; these may contain sensitive names. JSON escapes control characters.
Console output uses UTF-8 and escapes terminal control characters. HTML escapes all source-derived
strings and does not render source Markdown.

## CI integration

```yaml
- run: python -m pip install 'git+https://github.com/Nithinfgs/skillspine.git@v0.1.0'
- run: skillspine ./skills --layout isolated --format json --output skill-report.json
```

Run against an unchanging checkout. No API keys or model calls are required. A
finding returns exit 1 after writing the report. Invalid or incomplete scans return
exit 2. Supply only the intended collection root; repository-level shared references
outside that root will correctly appear as escaping references.
