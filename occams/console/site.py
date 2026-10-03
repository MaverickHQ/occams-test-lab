"""``python -m occams site`` — the lab's pages as one static site (M15.2).

Everything under ``docs/`` that a reader with no code should see, as HTML
with no script and no network reference, in the console's colours and both
themes: the console and the programme page copied as they are, every survey
page beside its readiness table, and every document — the conclusions, the
integrity write-up, the runbook, the setup path, the M0 evidence, the ADRs
and the Drafts — rendered from Markdown by the small renderer below, which
knows the subset these documents use and escapes everything else. Links
between documents stay relative and point at the rendered pages. The build
runs the publication check on every page it writes and refuses to finish
if one fails; publishing the result is a recorded decision (R7), not this
command's.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / "docs"

STYLE = """:root{color-scheme:light;--bg:#F7F6F2;--card:#FFFFFF;--ink:#182220;--sub:#64757A;--line:#D5DCDA;--rule:#E6EBE9;--accent:#2F6B5E;
--serif:Georgia,"Iowan Old Style","Palatino Linotype",serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#121A1B;--card:#192425;--ink:#E4ECEA;--sub:#93A6A8;--line:#2B3A3B;--rule:#22302F;--accent:#7FC0B0}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#121A1B;--card:#192425;--ink:#E4ECEA;--sub:#93A6A8;--line:#2B3A3B;--rule:#22302F;--accent:#7FC0B0}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--serif);font-variant-numeric:tabular-nums}
main{max-width:52rem;margin:0 auto;padding:32px 16px 64px}
h1{font-size:1.7rem;line-height:1.25;text-wrap:balance;margin:0 0 16px}h2{font-size:1.25rem;margin:36px 0 10px;text-wrap:balance}h3{font-size:1.05rem;margin:24px 0 8px}
p,li{max-width:65ch}a{color:var(--accent)}code{font-family:var(--mono);font-size:.86em;background:var(--card);border:1px solid var(--rule);border-radius:3px;padding:0 3px}
pre{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px;overflow-x:auto;font-family:var(--mono);font-size:.84em;line-height:1.45}pre code{border:0;padding:0;background:none}
blockquote{margin:12px 0;padding:2px 16px;border-left:3px solid var(--line);color:var(--sub)}blockquote p{max-width:60ch}
.wrap{overflow-x:auto}table{border-collapse:collapse;font-size:.92em;margin:12px 0}th,td{text-align:left;vertical-align:top;padding:6px 10px;border-bottom:1px solid var(--rule)}th{color:var(--sub);font-weight:600;border-bottom:1px solid var(--line)}
hr{border:0;border-top:1px solid var(--line);margin:28px 0}.crumb{color:var(--sub);font-size:.9em;margin-bottom:20px}.crumb a{color:var(--sub)}
.front{color:var(--sub);font-size:.88em;border:1px solid var(--rule);border-radius:6px;padding:8px 12px;margin:0 0 20px;font-family:var(--mono);white-space:pre-wrap}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));gap:12px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px}.card h3{margin:0 0 6px}.card p{margin:0;color:var(--sub);font-size:.92em}
ul.plain{list-style:none;padding:0}ul.plain li{padding:3px 0;border-bottom:1px solid var(--rule)}"""


# ---- a small Markdown renderer for the subset the documents use ----------------------------------

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_SCHEME = re.compile(r"(?i)\bhttps?://")       # a URL in a document is a reference: the scheme goes, the host and path stay as text


def _inline(text: str, *, depth: int) -> str:
    """Escape first, then the four inline forms; a code span's contents stay literal."""
    parts = _INLINE_CODE.split(text)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f"<code>{html.escape(_SCHEME.sub('', part))}</code>")
            continue
        s = html.escape(part, quote=False)
        s = _BOLD.sub(r"<strong>\1</strong>", s)
        s = _ITALIC.sub(r"<em>\1</em>", s)
        s = _LINK.sub(lambda m: _link(m.group(1), m.group(2), depth), s)    # an external link becomes its text first …
        out.append(_SCHEME.sub("", s))                                          # … then any bare URL loses its scheme
    return "".join(out)


def _link(text: str, href: str, depth: int) -> str:
    """Relative links only: a document's ``.md`` becomes its rendered page; an external
    reference is not a link on a self-contained page — the text stays, the href goes."""
    if re.match(r"(?i)^[a-z]+:", href) or href.startswith("//"):
        return text
    target, _, frag = href.partition("#")
    if target.endswith(".md"):
        target = target[:-3] + ".html"
    return f'<a href="{html.escape(target + ("#" + frag if frag else ""), quote=True)}">{text}</a>'


def render_markdown(text: str, *, depth: int = 0) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    if lines and lines[0].strip() == "---":                   # front matter, shown as a block, never parsed
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            j += 1
        out.append('<div class="front">' + html.escape("\n".join(lines[1:j])) + "</div>")
        i = j + 1
    para: list[str] = []

    def flush():
        if para:
            out.append("<p>" + _inline(" ".join(s.strip() for s in para), depth=depth) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("```"):
            flush()
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            out.append("<pre><code>" + html.escape(_SCHEME.sub("", "\n".join(lines[i + 1:j]))) + "</code></pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush()
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2).strip(), depth=depth)}</h{level}>")
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,})$", s):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if s.startswith(">"):
            flush()
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(lines[i].strip()[1:].lstrip())
                i += 1
            out.append("<blockquote>" + render_markdown("\n".join(block), depth=depth) + "</blockquote>")
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            header, body = cells[0], [r for r in cells[1:] if not all(re.match(r"^:?-{2,}:?$", c) for c in r)]
            t = "<div class=\"wrap\"><table><tr>" + "".join(f"<th>{_inline(c, depth=depth)}</th>" for c in header) + "</tr>"
            for r in body:
                t += "<tr>" + "".join(f"<td>{_inline(c, depth=depth)}</td>" for c in r) + "</tr>"
            out.append(t + "</table></div>")
            continue
        m = re.match(r"^(\s*)([-*]|\d+[.)])\s+(.*)$", line)
        if m:
            flush()
            ordered = m.group(2)[0].isdigit()
            items = []
            while i < len(lines):
                mm = re.match(r"^(\s*)([-*]|\d+[.)])\s+(.*)$", lines[i])
                if mm and (mm.group(2)[0].isdigit()) == ordered:
                    items.append(mm.group(3).strip())
                    i += 1
                elif lines[i].startswith("  ") and lines[i].strip() and items:     # a wrapped item
                    items[-1] += " " + lines[i].strip()
                    i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(x, depth=depth)}</li>" for x in items) + f"</{tag}>")
            continue
        para.append(line)
        i += 1
    flush()
    return "\n".join(out)


def page(title: str, body: str, *, crumb: str = "", depth: int = 0) -> str:
    home = "../" * depth + "index.html"
    nav = f'<div class="crumb"><a href="{home}">Occams</a>{(" · " + crumb) if crumb else ""}</div>'
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)}</title><style>{STYLE}</style></head><body><main>{nav}{body}</main></body></html>")


def _title_of(md: str, fallback: str) -> str:
    for line in md.splitlines():
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            return re.sub(r"[`*]", "", m.group(1)).strip()
    return fallback


# ---- the build --------------------------------------------------------------------------------

def build_site(docs: Path = DOCS, out: Path = ROOT / "build" / "site") -> dict:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    written: list[Path] = []
    sections: dict[str, list[tuple[str, str, str]]] = {"Pages": [], "Conclusions": [], "Surveys": [], "Documents": [],
                                                       "Decisions (ADRs)": [], "Drafts — no standing": []}
    for src in sorted(docs.rglob("*.html")):
        rel = src.relative_to(docs)
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out / rel)
        written.append(out / rel)
        label = {"console.html": "The research console — every record, the controls recomputed",
                 "programme.html": "The programme page — what was searched, what it cost, what was found"}.get(str(rel))
        if label:
            sections["Pages"].append((str(rel), label.split(" — ")[0], label.split(" — ")[1]))
        elif rel.parts[0] == "surveys":
            sections["Surveys"].append((str(rel), f"Survey {rel.stem}", "every cell on the definition partition, zero alpha"))
    for src in sorted(docs.rglob("*.md")):
        rel = src.relative_to(docs).with_suffix(".html")
        depth = len(rel.parts) - 1
        md = src.read_text(encoding="utf-8")
        title = _title_of(md, src.stem)
        crumb = " / ".join(rel.parts[:-1]) if depth else ""
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_text(page(title, render_markdown(md, depth=depth), crumb=crumb, depth=depth), encoding="utf-8")
        written.append(out / rel)
        key = ("Conclusions" if "CONCLUSION" in src.name else "Surveys" if rel.parts[0] == "surveys"
               else "Decisions (ADRs)" if rel.parts[0] == "adr" else "Drafts — no standing" if rel.parts[0] == "drafts" else "Documents")
        sections[key].append((str(rel), title, ""))
    body = ["<h1>Occams — a falsification lab for retail trading hypotheses</h1>",
            "<p>Three programmes, six questions, five verdicts — four null, one supported whose entry added nothing — and one refusal "
            "at measurement. Every page here is rendered from a hash-chained Register; none carries a script, a network reference "
            "or a money figure. The lab's product is its refusals.</p>"]
    for name, items in sections.items():
        if not items:
            continue
        body.append(f"<h2>{html.escape(name)}</h2>")
        if name in ("Pages", "Conclusions"):
            body.append('<div class="grid">' + "".join(
                f'<div class="card"><h3><a href="{html.escape(h, quote=True)}">{html.escape(t)}</a></h3><p>{html.escape(d)}</p></div>'
                for h, t, d in items) + "</div>")
        else:
            body.append('<ul class="plain">' + "".join(f'<li><a href="{html.escape(h, quote=True)}">{html.escape(t)}</a></li>' for h, t, _d in items) + "</ul>")
    index = out / "index.html"
    index.write_text(page("Occams", "\n".join(body)), encoding="utf-8")
    written.append(index)
    return {"out": out, "pages": len(written)}


def check_site(out: Path) -> list[str]:
    """The publication check on every page the build wrote (M11.7): refused, not published."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_prepublish", ROOT / "tools" / "prepublish.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    decisions = mod.load_decisions()
    problems: list[str] = []
    for p in sorted(out.rglob("*.html")):
        rel = str(p.relative_to(out))
        source = "docs/" + rel[:-5] + ".md"                      # the document this page was rendered from, if any
        for problem in mod.check_page(p.read_text(encoding="utf-8"), name=rel):
            m = re.search(r"a broker's or venue's term \('([^']+)'\)", problem)
            kept = m and any(d.get("file") == source and d.get("check") == "broker term (R6)" and d.get("match") in ("*", m.group(1))
                             for d in decisions)
            if not kept:                                           # a term kept by the author's recorded decision in the source is kept on its page
                problems.append(problem)
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m occams site", description="the lab's pages as one static site under build/")
    ap.add_argument("--docs", type=Path, default=DOCS)
    ap.add_argument("--out", type=Path, default=ROOT / "build" / "site")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    res = build_site(a.docs, a.out)
    problems = check_site(a.out)
    if problems:
        for p in problems:
            print(f"REFUSED: {p}")
        print(f"site: {res['pages']} page(s) written to {a.out}, {len(problems)} refused by the publication check — nothing publishable until each is resolved (M15.3)")
        return 1
    print(f"site: {res['pages']} page(s) under {a.out} — no script, no network, no money; publishing is a recorded decision (R7)")
    return 0
