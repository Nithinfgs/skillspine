from skillspine.markdown import references


def test_commonmark_destinations_and_fences():
    text = """---
name: test
---
# Test

[inline](docs/a(b).md) ![image](assets/pic.png) [reference][r]

[r]: <docs/has space.md> "title"

```md
[not a dependency](fake.md)
```

[anchor](#heading) [url](https://example.org/) <https://example.org/autolink>
"""
    refs, external = references(text)
    assert [r.target for r in refs] == ["docs/a(b).md", "assets/pic.png", "docs/has space.md"]
    assert all(r.line == 6 for r in refs)
    assert external == 2


def test_frontmatter_and_inline_code_heuristics():
    text = """---
description: '[no](metadata.md)'
---
Read `references/a.md` and `scripts/check.py` but create `output.md`.
"""
    assert not references(text)[0]
    assert [r.target for r in references(text, True)[0]] == ["references/a.md", "scripts/check.py"]


def test_percent_encoding_query_and_unicode():
    refs, _ = references("[x](docs/caf%C3%A9.md?raw=1#hello)")
    assert refs[0].target == "docs/café.md"


def test_html_not_interpreted():
    assert not references('<img src="secret.txt"><script>alert(1)</script>')[0]
