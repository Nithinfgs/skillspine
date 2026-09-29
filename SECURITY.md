# Security policy

v0.1.x is the currently supported line. Report vulnerabilities through the
repository's **Security → Report a vulnerability** feature. Do not publish secrets
or private skill content in an issue. For ordinary bugs, use the issue template
with a minimal synthetic directory tree.

## Threat model

Skillspine is a read-only static analyzer. It does not execute skill instructions,
source scripts, subprocesses, YAML constructors or HTML from analyzed files. It
makes no network requests. Symlinks are rejected, external URLs are not fetched,
and inventory/file-size limits bound common accidental oversized scans. Nonregular
files are not read. Configuration is explicitly selected TOML with known keys.

HTML contains escaped path metadata, fixed local CSS/JavaScript and a restrictive
Content Security Policy with network connections disabled. There are no remote
fonts, analytics, script imports or API keys. JSON export is generated locally.
Output uses exclusive creation and refuses overwriting a file or output symlink.

## Limits

A clean report is not a security audit of a skill. No malware, prompt-injection,
secret-content or script-behavior detection is provided. The scan is not atomic;
do not use it as a security boundary against processes changing directories during
a scan. Use a stable checkout with appropriate OS isolation for hostile repositories.

Default exclusions are convenience filters, not a secret scrubber. Reports omit
source bodies and the absolute scan root, but references can themselves contain
absolute paths, usernames or sensitive filenames. Review all reports before sharing.

Dependency auditing is performed with pip-audit; unpublished Skillspine itself has
no package-advisory entry. Our tests cover path escapes, symlinks, control characters,
HTML/script injection, output overwrite refusal and unreadable/oversized files.
