"""M15.2 — the lab's pages as one static site: rendered from docs/ alone, no script, no
network, every link relative and resolving, every page through the publication check."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from occams.console.site import DOCS, build_site, check_site, main as site_main, render_markdown

ROOT = Path(__file__).resolve().parent.parent


def test_the_renderer_knows_the_subset_the_documents_use_and_escapes_the_rest():
    md = ("---\nstatus: DRAFT\n---\n# Title with `code`\n\nA paragraph with **bold**, *italic*, `x = <float>` and a "
          "[link](../RUNBOOK.md#a-burst) and [outside](https://example.org/x).\n\n"
          "| a | b |\n|---|---|\n| 1 | `2` |\n\n- one\n- two\n  wrapped\n\n1. first\n2. second\n\n> quoted **text**\n\n```bash\nmake check <x>\n```\n\n---\n")
    out = render_markdown(md, depth=1)
    assert '<div class="front">status: DRAFT</div>' in out and "<h1>Title with <code>code</code></h1>" in out
    assert "<strong>bold</strong>" in out and "<em>italic</em>" in out and "<code>x = &lt;float&gt;</code>" in out
    assert '<a href="../RUNBOOK.html#a-burst">link</a>' in out                     # a document link points at the rendered page
    assert "outside" in out and "example.org" not in out and "https://" not in out   # an external reference is text, not a link
    assert "<table>" in out and "<th>a</th>" in out and "<td><code>2</code></td>" in out and "---" not in out.split("<table>")[1].split("</table>")[0]
    assert "<ul><li>one</li><li>two wrapped</li></ul>" in out and "<ol><li>first</li><li>second</li></ol>" in out
    assert "<blockquote>" in out and "<strong>text</strong>" in out
    assert "<pre><code>make check &lt;x&gt;</code></pre>" in out and "<hr>" in out
    bare = render_markdown("see `https://x.y/z` and https://a.b/c in ```\nhttp://d.e\n```")
    assert "https://" not in bare and "http://" not in bare and "x.y/z" in bare and "a.b/c" in bare and "d.e" in bare
    assert "<script" not in out


@pytest.mark.slow
def test_the_site_builds_from_docs_alone_with_every_link_resolving_and_every_page_clean(tmp_path, capsys):
    res = build_site(DOCS, tmp_path / "site")
    out = tmp_path / "site"
    assert (out / "index.html").exists() and (out / "console.html").exists() and (out / "programme.html").exists()
    assert (out / "LAB-CONCLUSION.html").exists() and (out / "INTEGRITY.html").exists() and (out / "adr").is_dir()
    assert res["pages"] == len(list(out.rglob("*.html")))
    broken = []
    for p in out.rglob("*.html"):
        text = p.read_text(encoding="utf-8")
        assert "<script" not in text.lower() and "http://" not in text and "https://" not in text and "@import" not in text, p.name
        for href in re.findall(r'href="([^"]+)"', text):
            target = href.split("#")[0]
            if not target:
                continue
            if not (p.parent / target).resolve().exists():
                broken.append((str(p.relative_to(out)), href))
    assert not broken, broken[:10]
    assert check_site(out) == []                          # M15.3 resolved every hit: removed, or kept by the author's recorded decision
    assert site_main(["--docs", str(DOCS), "--out", str(tmp_path / "site2")]) == 0
    assert "publishing is a recorded decision (R7)" in capsys.readouterr().out


def test_a_page_the_publication_check_refuses_stops_the_build(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ok.md").write_text("# Fine\n\nnothing to see\n")
    (docs / "bad.md").write_text("# Bad\n\n<script>alert(1)</script>\n")     # escaped by the renderer, so it passes: the check is on the output
    (docs / "worse.html").write_text("<html><body><script>x()</script></body></html>")   # a copied page with a script is refused
    assert site_main(["--docs", str(docs), "--out", str(tmp_path / "site")]) == 1
    out = capsys.readouterr().out
    assert "REFUSED: worse.html" in out and "nothing publishable" in out
