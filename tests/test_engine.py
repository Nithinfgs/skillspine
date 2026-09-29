from pathlib import Path

import pytest

from skillspine.engine import normalize_changed, scan
from skillspine.models import ScanError


def put(root: Path, name: str, content: str = "# Reference\n") -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_shared_transitive_impact_and_layout(tmp_path):
    put(tmp_path, "skills/a/SKILL.md", "[ref](../../shared/a.md)")
    put(tmp_path, "skills/b/SKILL.md", "[ref](../../shared/b.md)")
    put(tmp_path, "skills/c/SKILL.md")
    put(tmp_path, "shared/a.md", "[b](b.md)")
    put(tmp_path, "shared/b.md")
    result = scan(tmp_path, changed=["shared/b.md"])
    a, b, c = result.skills
    assert not a.collection and not b.collection
    assert {f.code for f in a.isolated} == {"outside_skill"}
    assert a.impacts["shared/b.md"] == ["skills/a/SKILL.md", "shared/a.md", "shared/b.md"]
    assert b.impacts["shared/b.md"] == ["skills/b/SKILL.md", "shared/b.md"]
    assert not c.impacts and not c.isolated


def test_cycle_and_shortest_path(tmp_path):
    put(tmp_path, "SKILL.md", "[a](a.md) [b](b.md)")
    put(tmp_path, "a.md", "[b](b.md)")
    put(tmp_path, "b.md", "[entry](SKILL.md)")
    skill = scan(tmp_path, changed=["b.md"]).skills[0]
    assert skill.dependencies == ["a.md", "b.md"]
    assert skill.impacts["b.md"] == ["SKILL.md", "b.md"]
    assert not skill.collection and not skill.isolated


def test_missing_deleted_target_is_impacted(tmp_path):
    put(tmp_path, "SKILL.md", "[deleted](gone.md)")
    s = scan(tmp_path, changed=["gone.md"]).skills[0]
    assert s.collection[0].code == "missing"
    assert s.impacts["gone.md"] == ["SKILL.md", "gone.md"]


def test_exact_case_even_on_case_insensitive_host(tmp_path):
    put(tmp_path, "SKILL.md", "[wrong](references/guide.md)")
    put(tmp_path, "References/Guide.md")
    assert scan(tmp_path).skills[0].collection[0].code == "case_mismatch"


def test_symlinks_and_outside_never_read(tmp_path):
    put(tmp_path, "SKILL.md", "[file](link.md) [dir](alias/x.md) [outside](../outside.md)")
    try:
        (tmp_path / "link.md").symlink_to(tmp_path.parent / "outside.md")
        (tmp_path / "alias").symlink_to(tmp_path.parent, target_is_directory=True)
    except OSError:
        pytest.skip("Host does not permit symlinks")
    codes = {f.code for f in scan(tmp_path).skills[0].collection}
    assert codes == {"symlink", "outside_collection"}


def test_directory_excluded_nonportable_and_external(tmp_path):
    put(
        tmp_path,
        "SKILL.md",
        "[dir](refs/) [env](.env) [win](C:/secret.md) "
        "[root](/file.md) [remote](https://example.org/x) [encoded](%2e%2e/out.md)",
    )
    (tmp_path / "refs").mkdir()
    put(tmp_path, ".env", "PRIVATE")
    r = scan(tmp_path)
    assert {f.code for f in r.skills[0].collection} == {
        "directory",
        "excluded",
        "nonportable_path",
        "outside_collection",
    }
    assert r.external_links == 1
    assert "PRIVATE" not in str(r.to_dict())


def test_only_reachable_markdown_read_and_assets_are_leaves(tmp_path):
    put(tmp_path, "SKILL.md", "[asset](data.bin)")
    (tmp_path / "data.bin").write_bytes(b"\xff\xff")
    (tmp_path / "unlinked.md").write_bytes(b"\xff\xff")
    assert scan(tmp_path).skills[0].dependencies == ["data.bin"]


def test_hidden_skill_directories_are_discovered(tmp_path):
    put(tmp_path, ".agents/skills/hello/SKILL.md")
    put(tmp_path, "node_modules/ignored/SKILL.md")
    assert len(scan(tmp_path).skills) == 1


def test_resource_limits_and_empty_root(tmp_path):
    with pytest.raises(ScanError, match="No regular"):
        scan(tmp_path)
    put(tmp_path, "SKILL.md", "x" * 101)
    with pytest.raises(ScanError, match="Markdown exceeds"):
        scan(tmp_path, max_markdown_bytes=100)
    put(tmp_path, "extra.md")
    with pytest.raises(ScanError, match="Inventory exceeds"):
        scan(tmp_path, max_files=1)
    with pytest.raises(ScanError, match="positive"):
        scan(tmp_path, max_files=0)


def test_invalid_utf8_is_error_not_clean(tmp_path):
    (tmp_path / "SKILL.md").write_bytes(b"\xff")
    with pytest.raises(ScanError, match="UTF-8"):
        scan(tmp_path)


@pytest.mark.parametrize("path", ["../escape", "/absolute", "C:/file", "a\\b", ".", "", "a\x00"])
def test_changed_path_validation(path):
    with pytest.raises(ScanError):
        normalize_changed([path])


def test_deterministic_report(tmp_path):
    put(tmp_path, "SKILL.md", "[b](b.md) [a](a.md)")
    put(tmp_path, "b.md")
    put(tmp_path, "a.md")
    assert (
        scan(tmp_path, changed=["b.md", "a.md"]).to_dict()
        == scan(tmp_path, changed=["a.md", "./b.md", "b.md"]).to_dict()
    )


def test_opt_in_code_paths(tmp_path):
    put(tmp_path, "SKILL.md", "Read `references/a.md`.")
    assert not scan(tmp_path).edges
    assert scan(tmp_path, code_paths=True).edges[0].kind == "code"


def test_no_machine_absolute_paths_in_report(tmp_path):
    put(tmp_path, "SKILL.md", "[ref](local.md)")
    report = scan(tmp_path).to_dict()
    assert str(tmp_path) not in str(report)


def test_excluded_subtree_and_custom_glob(tmp_path):
    put(tmp_path, "SKILL.md", "[ref](generated/a.md)")
    put(tmp_path, "generated/a.md")
    assert scan(tmp_path, exclude=("generated",)).skills[0].collection[0].code == "excluded"
