#!/usr/bin/env python3
"""
Builds the PvpBot wiki: every content/*.html page is wrapped in the site layout (sidebar, search, table of contents,
previous/next) and written to the repository root, where GitHub Pages serves it as is. Python 3 standard library only.

    python3 build.py

Content pages start with a small header:

    ---
    title: Commands
    section: Reference
    order: 20
    lead: One sentence under the title.
    ---

and may use {{settings:<group>}} to insert the settings table of one group, generated from content/data/.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
SITE_NAME = "PvpBot docs"

# Icons are inline SVG (no icon font, no emoji): 20px, stroked with the current text colour.
_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"{cls}>{body}</svg>'
ICON_MENU = _SVG.format(cls="", body='<path d="M4 7h16M4 12h16M4 17h16"/>')
ICON_SEARCH = _SVG.format(cls="", body='<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4-4"/>')
ICON_MOON = _SVG.format(cls=' class="i-moon"', body='<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>')
ICON_SUN = _SVG.format(cls=' class="i-sun"', body='<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>')
# The favicon: the letter P in a square, in the accent colour.
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' "
           "fill='%23a3302a'/%3E%3Cpath d='M11 24V8h6.5a4.5 4.5 0 0 1 0 9H11' fill='none' stroke='%23fff' stroke-width='3'/%3E%3C/svg%3E")
SECTIONS = ["Getting started", "Reference", "Features", "Help"]


def parse(path):
    raw = path.read_text(encoding="utf-8")
    meta = {}
    body = raw
    if raw.startswith("---"):
        head, body = raw[3:].split("\n---", 1)
        for line in head.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    slug = path.stem
    return {
        "slug": slug,
        "url": "index.html" if slug == "index" else slug + ".html",
        "title": meta.get("title", slug),
        "section": meta.get("section", "Features"),
        "order": int(meta.get("order", "100")),
        "lead": meta.get("lead", ""),
        "hero": meta.get("hero", "") == "true",
        "body": body.strip(),
    }


def slugify(text, taken):
    s = re.sub(r"<[^>]+>", "", text)
    s = html.unescape(s).lower()
    s = re.sub(r"[àá]", "a", s)
    s = re.sub(r"[èé]", "e", s)
    s = re.sub(r"[ìí]", "i", s)
    s = re.sub(r"[òó]", "o", s)
    s = re.sub(r"[ùú]", "u", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "sezione"
    base, n = s, 2
    while s in taken:
        s = f"{base}-{n}"
        n += 1
    taken.add(s)
    return s


def strip_tags(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


# ---- the settings tables ------------------------------------------------------------------------

def settings_tables():
    schema = json.loads((CONTENT / "data" / "settings-schema.json").read_text(encoding="utf-8"))
    described = json.loads((CONTENT / "data" / "settings-text.json").read_text(encoding="utf-8"))
    code_defaults = described.get("_code_defaults", {})
    groups = {}
    for e in schema:
        groups.setdefault(e["group"], []).append(e)

    def fmt_default(e):
        d = e["default"]
        if d is None:
            d = code_defaults.get(e["key"])
        if isinstance(d, bool):
            return "true" if d else "false"
        return "—" if d is None else str(d)

    def fmt_range(e):
        if e["type"] == "BOOL":
            return "true / false"
        lo, hi = float(e["min"]), float(e["max"])
        f = (lambda x: str(int(x))) if e["type"] == "INT" else (lambda x: ("%g" % x))
        return f"{f(lo)} – {f(hi)}"

    tables = {}
    for group, entries in groups.items():
        rows = []
        for e in entries:
            desc = described.get(e["key"], e["help"])
            rows.append(
                "<tr><td><code>{k}</code></td><td class=\"def\"><code>{d}</code></td><td class=\"def\">{r}</td><td>{h}</td></tr>".format(
                    k=html.escape(e["key"]), d=html.escape(fmt_default(e)), r=html.escape(fmt_range(e)), h=desc))
        tables[group] = ("<div class=\"table-wrap\"><table class=\"settings\"><thead><tr><th>Setting</th><th>Default</th><th>Values</th>"
                         "<th>What it does</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
    return tables


# ---- layout -------------------------------------------------------------------------------------

def sidebar(pages, current):
    out = []
    for section in SECTIONS:
        items = [p for p in pages if p["section"] == section]
        if not items:
            continue
        out.append(f"<h4>{html.escape(section)}</h4>")
        for p in items:
            cls = ' class="active"' if p is current else ""
            out.append(f'<a href="{p["url"]}"{cls}>{html.escape(p["title"])}</a>')
    return "\n".join(out)


HEAD_SCRIPT = ("<script>try{var t=localStorage.getItem('pvpbot-theme');if(t)document.documentElement.setAttribute('data-theme',t)}"
               "catch(e){}</script>")


def page_html(p, pages, body, toc):
    i = pages.index(p)
    prev_p = pages[i - 1] if i > 0 else None
    next_p = pages[i + 1] if i + 1 < len(pages) else None
    pager = '<nav class="pager">'
    pager += (f'<a class="prev" href="{prev_p["url"]}"><small>← Previous</small>{html.escape(prev_p["title"])}</a>'
              if prev_p else "<span></span>")
    pager += (f'<a class="next" href="{next_p["url"]}"><small>Next →</small>{html.escape(next_p["title"])}</a>'
              if next_p else "<span></span>")
    pager += "</nav>"
    toc_html = ""
    if toc:
        sub = ' class="sub"'
        toc_html = "<h5>On this page</h5>" + "".join(
            f'<a href="#{hid}"{sub if lvl == 3 else ""}>{html.escape(text)}</a>' for lvl, hid, text in toc)
    header = ""
    if not p["hero"]:
        header = (f'<div class="crumb">{html.escape(p["section"])}</div><h1>{html.escape(p["title"])}</h1>'
                  + (f'<p class="lead">{p["lead"]}</p>' if p["lead"] else ""))
    title = "PvpBot documentation" if p["slug"] == "index" else f'{p["title"]} · {SITE_NAME}'
    next_cls = ' class="active"' if p["slug"] == "next-update" else ""
    desc = strip_tags(p["lead"]) or "Documentation for PvpBot, the PvP bot plugin for Paper and Spigot."
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">
<link rel="stylesheet" href="assets/style.css">
{HEAD_SCRIPT}
</head>
<body>
<header class="topbar">
  <button class="icon-btn menu-btn" id="menu" aria-label="Menu">{ICON_MENU}</button>
  <a class="brand" href="index.html">PvpBot<span class="brand-sub">docs</span></a>
  <nav class="topnav">
    <a href="next-update.html"{next_cls}>Next update</a>
    <a href="https://modrinth.com/plugin/pvp-bot-plugin-pvpbp">Download</a>
  </nav>
  <div class="search">
    <span class="icon">{ICON_SEARCH}</span>
    <input id="q" type="search" placeholder="Search" autocomplete="off" aria-label="Search">
    <kbd>/</kbd>
    <div class="results" id="results"></div>
  </div>
  <button class="icon-btn" id="theme" aria-label="Light or dark theme">{ICON_MOON}{ICON_SUN}</button>
</header>
<div class="layout">
<nav class="sidebar">
{sidebar(pages, p)}
</nav>
<main class="content">
<article>
{header}
{body}
</article>
{pager}
<footer class="foot"><span>PvpBot · Paper and Spigot 1.21.11 / 26.2</span><a href="https://modrinth.com/plugin/pvp-bot-plugin-pvpbp">Modrinth</a><a href="https://github.com/Nantag/Plugin-PvP-Bot-doc">Edit these docs on GitHub</a></footer>
</main>
<aside class="toc">{toc_html}</aside>
</div>
<script src="assets/search-index.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""


def main():
    pages = [parse(f) for f in sorted(CONTENT.glob("*.html"))]
    pages.sort(key=lambda p: (SECTIONS.index(p["section"]) if p["section"] in SECTIONS else 99, p["order"], p["title"]))
    tables = settings_tables()
    index = []
    for p in pages:
        body = re.sub(r"\{\{settings:([a-z]+)\}\}", lambda m: tables.get(m.group(1), ""), p["body"])
        taken, toc = set(), []

        def add_id(m):
            level, attrs, inner = int(m.group(1)), m.group(2) or "", m.group(3)
            idm = re.search(r'id="([^"]+)"', attrs)
            hid = idm.group(1) if idm else slugify(inner, taken)
            if idm:
                taken.add(hid)
            text = strip_tags(inner)
            toc.append((level, hid, text))
            attrs = attrs if idm else f'{attrs} id="{hid}"'
            return f'<h{level}{attrs}>{inner}<a class="anchor" href="#{hid}" aria-hidden="true">#</a></h{level}>'

        body = re.sub(r"<h([23])((?:\s[^>]*)?)>(.*?)</h\1>", add_id, body, flags=re.S)
        (ROOT / p["url"]).write_text(page_html(p, pages, body, toc), encoding="utf-8")

        # search entries: the page itself, then each section of it
        parts = re.split(r'(<h[23][^>]*id="[^"]+"[^>]*>.*?</h[23]>)', body, flags=re.S)
        index.append({"title": p["title"], "page": p["section"], "url": p["url"],
                      "text": strip_tags(p["lead"] + " " + parts[0])[:600]})
        for j in range(1, len(parts), 2):
            hid = re.search(r'id="([^"]+)"', parts[j]).group(1)
            title = strip_tags(re.sub(r'<a class="anchor".*?</a>', "", parts[j]))
            text = strip_tags(parts[j + 1] if j + 1 < len(parts) else "")[:900]
            index.append({"title": title, "page": p["title"], "url": f'{p["url"]}#{hid}', "text": text})
    (ROOT / "assets" / "search-index.js").write_text(
        "window.PVPBOT_INDEX = " + json.dumps(index, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"{len(pages)} pages, {len(index)} search entries.")


if __name__ == "__main__":
    main()
