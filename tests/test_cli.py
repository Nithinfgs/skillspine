import io
import json
from pathlib import Path

from skillspine.cli import main
from skillspine.engine import scan
from skillspine.report import html_report, text_report


def test_cli_exit_modes_and_json(tmp_path, capsys):
    (tmp_path / "SKILL.md").write_text("[missing](gone.md)")
    assert main([str(tmp_path)]) == 1
    assert main([str(tmp_path), "--fail-on", "never"]) == 0
    assert main([str(tmp_path), "--changed", "gone.md", "--fail-on", "impact"]) == 1
    capsys.readouterr()
    assert main([str(tmp_path), "--format", "json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["schema_version"] == 1
    assert report["skills"][0]["collection"][0]["code"] == "missing"


def test_output_exclusive_and_empty_error(tmp_path, capsys):
    assert main([str(tmp_path)]) == 2
    assert "No regular" in capsys.readouterr().err
    (tmp_path / "SKILL.md").write_text("# Hello")
    output = tmp_path / "report.html"
    assert main([str(tmp_path), "--format", "html", "--output", str(output)]) == 0
    before = output.read_text(encoding="utf-8")
    assert main([str(tmp_path), "--output", str(output)]) == 2
    assert output.read_text(encoding="utf-8") == before
    assert main([str(tmp_path), "--output", str(tmp_path / "SKILL.md")]) == 2
    assert (tmp_path / "SKILL.md").read_text() == "# Hello"


def test_config_validation_and_precedence(tmp_path, capsys):
    (tmp_path / "SKILL.md").write_text("Read `references/missing.md`.")
    cfg = tmp_path / "config.toml"
    cfg.write_text("code_paths = true\n")
    assert main([str(tmp_path), "--config", str(cfg)]) == 1
    for content in [
        "unknown = true",
        'code_paths = "yes"',
        'exclude = "x"',
        "max_files = false",
        "max_markdown_bytes = -1",
        "invalid=",
    ]:
        cfg.write_text(content)
        assert main([str(tmp_path), "--config", str(cfg)]) == 2
        assert "skillspine:" in capsys.readouterr().err


def test_html_escapes_untrusted_paths(tmp_path):
    (tmp_path / "SKILL.md").write_text("[hostile](%3Cscript%3Ealert%281%29%3C/script%3E)")
    report = html_report(scan(tmp_path), "isolated")
    assert "<script>alert(1)" not in report
    assert "&lt;script&gt;" in report
    assert "\\u003cscript\\u003e" in report
    assert "connect-src 'none'" in report
    assert 'value="isolated" selected' in report


def test_text_sanitizes_controls(tmp_path):
    (tmp_path / "SKILL.md").write_text("[bad](bad%1Bname.md)")
    assert "\x1b" not in text_report(scan(tmp_path), "isolated")


def test_example_collection_matches_pitch():
    root = Path(__file__).resolve().parents[1] / "examples" / "collection"
    report = scan(root, changed=["shared/rubric.md"])
    assert len(report.skills) == 3
    assert sum(bool(s.impacts) for s in report.skills) == 2
    assert sum(bool(s.isolated) for s in report.skills) == 2
    assert not any(s.collection for s in report.skills)


def test_stdout_uses_utf8_even_with_legacy_encoding(tmp_path, monkeypatch):
    (tmp_path / "SKILL.md").write_text("# Hello", encoding="utf-8")
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="ascii")
    monkeypatch.setattr("sys.stdout", stream)
    assert main([str(tmp_path)]) == 0
    stream.flush()
    assert "SKILLSPINE ·" in buffer.getvalue().decode("utf-8")
