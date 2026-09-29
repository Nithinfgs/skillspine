"""Plain text and standalone HTML renderers. Source Markdown is never rendered."""

import html
import json
from collections import Counter
from importlib.resources import files

from .models import Report


def text_report(report: Report, layout: str) -> str:
    lines = ["SKILLSPINE · dependency & install report", ""]
    for skill in report.skills:
        findings = skill.isolated if layout == "isolated" else skill.collection
        state = f"{len(findings)} finding(s)" if findings else "PASS"
        lines.append(f"{state:16} {skill.entry} · {len(skill.dependencies)} dependencies")
        for f in findings:
            lines.append(f"  {f.code}: {f.source}:{f.line} → {f.target}")
            lines.append(f"    {f.message}")
        for changed, chain in skill.impacts.items():
            lines.append(f"  IMPACT {changed}: {' → '.join(chain)}")
    affected = sum(bool(s.impacts) for s in report.skills)
    lines.extend(
        [
            "",
            f"{len(report.skills)} skills · {len(report.edges)} reference edges · "
            f"{report.external_links} external links not fetched",
            f"Layout: {layout} · {affected} affected skill(s)",
            "Static file references only; not a runtime or security certification.",
        ]
    )
    # Terminal control characters in filenames must not become escape sequences.
    return "\n".join(lines).translate({i: f"\\x{i:02x}" for i in range(32) if i not in {10}})


def html_report(report: Report, layout: str) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value), quote=True)

    rows = []
    for skill in report.skills:
        panels = []
        for mode in ("collection", "isolated"):
            findings = getattr(skill, mode)
            items = "".join(
                f'<li><span class="tag">{esc(f.code.replace("_", " "))}</span>'
                f"<code>{esc(f.source)}:{f.line} → {esc(f.target)}</code>"
                f"<p>{esc(f.message)}</p><small>Via {esc(' → '.join(f.chain))}</small></li>"
                for f in findings
            )
            panels.append(
                f'<div class="mode-panel" data-mode="{mode}">'
                + (
                    f'<ul class="findings">{items}</ul>'
                    if items
                    else '<p class="pass">✓ All discovered file references are available.</p>'
                )
                + "</div>"
            )
        chains = "".join(
            "<li>"
            + ' <span class="arrow">→</span> '.join(f"<code>{esc(p)}</code>" for p in chain)
            + "</li>"
            for chain in skill.impacts.values()
        )
        dependencies = "".join(f"<li><code>{esc(p)}</code></li>" for p in skill.dependencies)
        rows.append(
            f'<article class="skill" data-affected="{str(bool(skill.impacts)).lower()}">'
            f'<div class="skill-heading"><div><span class="eyebrow">SKILL ENTRYPOINT</span>'
            f'<h3>{esc(skill.entry)}</h3></div><span class="count">'
            f"{len(skill.dependencies)} dependencies</span></div>"
            + "".join(
                f'<span class="mode-panel status {"warn" if getattr(skill, m) else "good"}" '
                f'data-mode="{m}">{len(getattr(skill, m))} findings · {m}</span>'
                for m in ("collection", "isolated")
            )
            + (
                f'<div class="impact"><b>Affected by your change</b><ol>{chains}</ol></div>'
                if chains
                else ""
            )
            + "".join(panels)
            + f"<details><summary>Inspect dependency list ({len(skill.dependencies)})</summary>"
            f'<ul class="dependency-list">{dependencies or "<li>No local dependencies.</li>"}</ul>'
            "</details></article>"
        )
    usage = Counter(dep for skill in report.skills for dep in skill.dependencies)
    shared = [(path, count) for path, count in usage.items() if count > 1]
    shared.sort(key=lambda item: (-item[1], item[0]))
    shared_html = (
        "".join(
            f'<div class="shared"><code>{esc(path)}</code><span>{count} skills</span>'
            f'<div class="bar" style="width:{count / len(report.skills) * 100:.1f}%"></div></div>'
            for path, count in shared[:12]
        )
        or "<p>No shared file dependencies discovered.</p>"
    )
    payload = (
        json.dumps(report.to_dict(), ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return (
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; img-src data:; base-uri 'none'; form-action 'none'">
<title>Skillspine · Dependency report</title><style>
"""
        + files("skillspine").joinpath("static/report.css").read_text(encoding="utf-8")
        + """</style></head><body><main><header><div class="brand"><span class="mark">⋮</span>skillspine</div>
<span class="local">LOCAL ANALYSIS / NO UPLOADS</span></header><section class="hero"><span class="eyebrow">THE DEPENDENCIES BEHIND YOUR SKILLS</span>
<h1>One shared file.<br>Know every skill it touches.</h1><p class="lede">Follow the reference chain. See what a change reaches, and what disappears when a skill is installed on its own.</p></section>
<div class="stats">"""
        + "".join(
            f'<div class="stat"><b>{count}</b><span>{label}</span></div>'
            for count, label in [
                (len(report.skills), "skills discovered"),
                (len(report.edges), "reference edges"),
                (sum(bool(s.impacts) for s in report.skills), "skills affected by changes"),
                (sum(bool(s.isolated) for s in report.skills), "skills with isolated findings"),
            ]
        )
        + """</div>
<div class="grid"><section><h2>Installation & change impact</h2><div class="controls">
<label>Find a skill or dependency<input id="search" type="search" placeholder="Search paths…"></label>
<label>Installation layout<select id="layout"><option value="isolated" """
        + ("selected" if layout == "isolated" else "")
        + """>Isolated skill folder</option><option value="collection" """
        + ("selected" if layout == "collection" else "")
        + """>Full collection</option></select></label>
<label class="checkbox"><input id="affected" type="checkbox">Affected only</label></div>
<p id="visible-count" aria-live="polite"></p><div id="skills">"""
        + "".join(rows)
        + """</div>
<p id="empty" hidden>No matching skills. Clear the search or turn off “Affected only”.</p></section>
<aside><h2>Shared dependency reach</h2><p>Files reached by multiple skills. Counts reflect static reference paths.</p>"""
        + shared_html
        + """
<div class="note"><strong>READ THE RESULT CORRECTLY</strong><p>Availability is a file check, not proof a skill runs correctly. Scripts are leaves; external links are not fetched. Source locations point to the containing Markdown block.</p>
<p>Reports contain relative filenames and dependency paths. Review them before sharing.</p><button id="download" type="button">Download JSON</button></div></aside></div>
<footer>Skillspine 0.1.0 · Static analysis · No telemetry · """
        + str(report.external_links)
        + """ external links skipped · """
        + ("Code-path heuristics enabled" if report.code_paths else "Explicit Markdown links only")
        + """</footer></main>
<script type="application/json" id="report-data">"""
        + payload
        + """</script><script>
"""
        + files("skillspine").joinpath("static/report.js").read_text(encoding="utf-8")
        + """</script></body></html>"""
    )
