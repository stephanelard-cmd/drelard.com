#!/usr/bin/env python3
"""Génère toutes les pages HTML de drelard.com à partir de _src/.

Usage : python3 scripts/build.py           (régénère le site)
        python3 scripts/build.py --check   (échoue si une page générée n'est pas à jour)

Chaque page vit dans _src/pages/<slug>/ :
  meta.json  titre, description, données sociales, JSON-LD, fil d'Ariane, bloc de rendez-vous…
  body.part  contenu principal (HTML) ; marqueurs remplacés : {{portrait}}, <!-- article -->

Les fichiers HTML générés sont publiés tels quels par GitHub Pages :
ne pas les modifier à la main, modifier _src/ puis relancer ce script.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_src"
SITE = "https://drelard.com"
DOCTOLIB = "https://www.doctolib.fr/chirurgien-urologue/osny/stephane-elard"

OSNY = {
    "name": "Osny, CHP Sainte-Marie",
    "href": "/urologue-osny/",
    "street": "1 rue Christian Barnard",
    "city": "95520 Osny",
    "tel": "01 30 75 63 01",
    "tel_href": "tel:+33130756301",
}
ENGHIEN = {
    "name": "Enghien-les-Bains, cabinet médical",
    "href": "/urologue-enghien-les-bains/",
    "street": "8 rue de Malleville",
    "city": "95880 Enghien-les-Bains",
    "tel": "01 39 64 14 94",
    "tel_href": "tel:+33139641494",
}
NAV = [
    ("/urologie/", "Pathologies"),
    ("/urologue-osny/", "Osny"),
    ("/urologue-enghien-les-bains/", "Enghien-les-Bains"),
    ("/dr-stephane-elard/", "Le Dr Elard"),
    ("/rendez-vous/", "Contacts"),
]
FICHES = {
    "/adenome-prostate/": "Adénome de la prostate",
    "/cancer-prostate/": "Cancer de la prostate",
    "/calculs-urinaires/": "Calculs urinaires",
    "/prolapsus-genital/": "Prolapsus génital",
    "/urologie/": "Toutes les fiches d’urologie",
}
CSP = ("default-src 'self'; base-uri 'self'; object-src 'none'; frame-src 'none'; form-action 'none'; "
       "img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
       "font-src 'self'; connect-src 'self'")
SPECULATION = {"prerender": [{"where": {"and": [{"href_matches": "/*"}, {"not": {"href_matches": "/*.txt"}}]},
                              "eagerness": "moderate"}]}
PORTRAIT_WIDTHS = (360, 540, 720, 960)
PORTRAIT_SIZES = "(max-width: 859px) 88px, (max-width: 1200px) 30vw, 380px"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def minify_css(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    css = re.sub(r":\s+", ":", css)
    css = css.replace(";}", "}")
    # « and(...) » des requêtes média exige des espaces : les restaurer
    css = re.sub(r"\)and\(", ") and (", css)
    return css.strip()


def srcset(ext: str) -> str:
    return ", ".join(f"/assets/img/dr-elard-{w}.{ext} {w}w" for w in PORTRAIT_WIDTHS)


def portrait(alt: str) -> str:
    return (
        '<figure class="hero__photo"><picture>'
        f'<source type="image/avif" srcset="{srcset("avif")}" sizes="{PORTRAIT_SIZES}">'
        f'<source type="image/webp" srcset="{srcset("webp")}" sizes="{PORTRAIT_SIZES}">'
        f'<img src="/assets/img/dr-elard-720.jpg" width="720" height="900" alt="{esc(alt)}" '
        'fetchpriority="high" decoding="async"></picture></figure>'
    )


def jsonld(block: dict) -> str:
    data = json.dumps(block["data"], ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    ident = f' id="{esc(block["id"])}"' if block.get("id") else ""
    return f'<script type="application/ld+json"{ident}>{data}</script>'


def head(meta: dict, css: str) -> str:
    out = [
        "<!doctype html>",
        '<html lang="fr">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">',
        f"<title>{esc(meta['title'])}</title>",
        f'<meta name="description" content="{esc(meta["description"])}">',
        f'<link rel="canonical" href="{esc(meta["canonical"])}">',
        '<link rel="preload" href="/assets/fonts/onest.woff2" as="font" type="font/woff2" crossorigin>',
    ]
    if meta.get("portrait"):
        out.append(f'<link rel="preload" as="image" type="image/avif" imagesrcset="{srcset("avif")}" '
                   f'imagesizes="{PORTRAIT_SIZES}" media="(min-width: 860px)" fetchpriority="high">')
    out += [
        f"<style>{css}</style>",
        '<meta name="theme-color" content="#0f1d36">',
        '<meta name="color-scheme" content="light">',
        f'<meta name="robots" content="{esc(meta.get("robots") or "index,follow")}">',
        '<meta name="author" content="Dr Stéphane Elard">',
        '<meta name="referrer" content="strict-origin-when-cross-origin">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">',
        '<link rel="manifest" href="/site.webmanifest">',
        '<link rel="contents" href="/plan-du-site/" title="Plan du site">',
        '<link rel="help" href="/accessibilite/" title="Accessibilité">',
        '<link rel="alternate" type="text/plain" href="/llms.txt" title="Résumé du site pour les agents et assistants">',
    ]
    out += meta.get("extra", [])
    for kind, name, content in meta.get("social", []):
        out.append(f'<meta {kind}="{esc(name)}" content="{esc(content)}">')
    out += [jsonld(b) for b in meta.get("jsonld", [])]
    out.append('<script type="speculationrules">'
               + json.dumps(SPECULATION, separators=(",", ":")) + "</script>")
    out.append("</head>")
    return "\n".join(out)


def header(current: str | None) -> str:
    def links() -> str:
        mark = ' aria-current="page"'
        return "".join(f'<a href="{href}"{mark if href == current else ""}>{label}</a>' for href, label in NAV)
    return (
        '<a class="skip" href="#main">Aller au contenu principal</a>\n'
        '<header class="hdr"><div class="wrap">'
        '<a class="brand" href="/"><b>Dr Stéphane Elard</b><span>Chirurgien urologue</span></a>'
        f'<nav class="nav" aria-label="Navigation principale">{links()}</nav>'
        f'<a class="btn btn--sm" href="{DOCTOLIB}">Prendre rendez-vous</a>'
        f'<details class="menu"><summary>Menu</summary><nav aria-label="Menu">{links()}'
        f'<a href="{DOCTOLIB}">Prendre rendez-vous sur Doctolib</a></nav></details>'
        "</div></header>"
    )


def crumbs(items: list[list[str]]) -> str:
    parts = []
    for i, (label, href) in enumerate(items):
        if i == len(items) - 1:
            parts.append(f'<li aria-current="page">{label}</li>')
        else:
            parts.append(f'<li><a href="{href}">{label}</a></li>')
    return f'<nav class="crumbs wrap" aria-label="Fil d’Ariane"><ol>{"".join(parts)}</ol></nav>'


def toc(article: str) -> str:
    entries = re.findall(r'<section class="part[^"]*" id="([^"]+)"[^>]*>\s*(?:<div class="head">)?\s*<h2[^>]*>(.*?)</h2>',
                         article, re.S)
    items = "".join(f'<li><a href="#{i}">{re.sub(r"<[^>]+>", "", t)}</a></li>' for i, t in entries)
    return ('<aside class="toc" aria-label="Sommaire"><p>Sur cette page</p>'
            f'<ol>{items}</ol><a class="btn btn--sm" href="{DOCTOLIB}">Prendre rendez-vous</a></aside>')


def place(site: dict, text: str, heading: str = "h3") -> str:
    return (
        f'<article class="place"><{heading}>{site["name"]}</{heading}>'
        f'<address>{site["street"]}<br>{site["city"]}</address>'
        f'<a class="tel" href="{site["tel_href"]}">{site["tel"]}</a>'
        f"<p>{text}</p>"
        f'<p class="go"><a href="{site["href"]}">Informations pratiques</a></p></article>'
    )


def book(meta: dict, url: str) -> str:
    b = meta.get("book")
    if not b:
        return ""
    tone = " book--white" if b.get("white") else ""
    out = [f'<section class="book{tone}" id="{b.get("id", "rendez-vous")}" aria-labelledby="book-title"><div class="wrap">',
           f'<div class="head"><h2 id="book-title">{b["title"]}</h2><p>{b["text"]}</p>'
           f'<div class="actions"><a class="btn" href="{DOCTOLIB}">Prendre rendez-vous sur Doctolib</a></div></div>',
           '<div class="places">', place(OSNY, b["osny"]), place(ENGHIEN, b["enghien"]), "</div>"]
    if b.get("note"):
        note_id = f' id="{b["note_id"]}"' if b.get("note_id") else ""
        out.append(f'<p class="note"{note_id}>{b["note"]}</p>')
    if meta.get("related"):
        links = "".join(f'<li><a href="{h}">{FICHES[h]}</a></li>' for h in meta["related"])
        out.append(f'<nav class="related" aria-label="Autres fiches d’information"><h2>Autres fiches d’information</h2>'
                   f'<ul class="linklist">{links}</ul></nav>')
    if meta.get("share"):
        from urllib.parse import quote
        u = quote(url, safe="")
        t = quote(meta["share"] + " " + url, safe="")
        out.append('<p class="share">Partager cette page :'
                   f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={u}">LinkedIn</a>'
                   f'<a href="https://www.facebook.com/sharer/sharer.php?u={u}">Facebook</a>'
                   f'<a href="https://wa.me/?text={t}">WhatsApp</a></p>')
    out.append("</div></section>")
    return "".join(out)


def footer(year: int) -> str:
    return (
        '<footer class="ftr"><div class="wrap"><div class="cols">'
        '<div class="about"><h2>Dr Stéphane Elard</h2><p>Chirurgien urologue et andrologue diplômé, '
        "ancien chef de clinique des Hôpitaux de Paris. Ce site informe sans remplacer une consultation : "
        "il ne pose aucun diagnostic.</p>"
        '<p><strong>Urgence :</strong> appelez le <a href="tel:15">15</a> ou le <a href="tel:112">112</a>.</p></div>'
        '<div id="contact"><h2>Consultations</h2>'
        f'<address><a href="{OSNY["href"]}">Osny, CHP Sainte-Marie</a><br>{OSNY["street"]}, {OSNY["city"]}<br>'
        f'<a href="{OSNY["tel_href"]}">{OSNY["tel"]}</a> · <a href="mailto:chir3osny@gmail.com">chir3osny@gmail.com</a></address>'
        f'<address><a href="{ENGHIEN["href"]}">Enghien-les-Bains</a><br>{ENGHIEN["street"]}, {ENGHIEN["city"]}<br>'
        f'<a href="{ENGHIEN["tel_href"]}">{ENGHIEN["tel"]}</a></address>'
        f'<p style="margin-top:1rem"><a href="{DOCTOLIB}">Prendre rendez-vous sur Doctolib</a></p></div>'
        '<nav aria-label="Liens utiles"><h2>Informations</h2><ul>'
        '<li><a href="/urologie/">Fiches d’information en urologie</a></li>'
        '<li><a href="/dr-stephane-elard/">Parcours et diplômes</a></li>'
        '<li><a href="/preparer-consultation/">Préparer votre consultation</a></li>'
        '<li><a href="/rendez-vous/">Rendez-vous et contacts</a></li>'
        '<li><a href="/plan-du-site/">Plan du site</a></li>'
        '<li><a href="/accessibilite/">Accessibilité</a></li>'
        '<li><a href="/llms.txt">Résumé texte du site</a></li></ul></nav>'
        "</div>"
        f'<p class="legal">© {year} Dr Stéphane Elard. RPPS 10001530970. SIREN 914103858. '
        "Secteur 2, adhérent à l’OPTAM-ACO. Hébergement technique : GitHub Pages (GitHub, Inc.). "
        "Ce site ne publie ni note, ni classement, ni témoignage de patient.</p>"
        "</div></footer>\n"
        f'<div class="bar"><a class="btn" href="{DOCTOLIB}">Rendez-vous en ligne</a>'
        '<a class="btn btn--line" href="#contact">Téléphones</a></div>'
    )


def render(slug: str, meta: dict, body: str, css: str, year: int) -> str:
    url = meta["canonical"]
    if "{{portrait}}" in body:
        body = body.replace("{{portrait}}", portrait(meta["portrait"]))
    if "<!-- article -->" in body:
        intro, article = body.split("<!-- article -->", 1)
        body = f'{intro}<div class="wrap doc">{toc(article)}<div class="article">{article}</div></div>'
    # Bandeau sombre d’en-tête : fil d’Ariane + premier bloc de la page (accueil ou titre)
    m = re.match(r'\s*(<header class="intro[^"]*">.*?</header>|<section class="hero[^"]*"[^>]*>.*?</section>)', body, re.S)
    if not m:
        raise SystemExit(f"{slug}: la page doit commencer par <header class=\"intro\"> ou <section class=\"hero\">")
    top = '<div class="top dark">' + (crumbs(meta["crumbs"]) if meta.get("crumbs") else "") + m.group(1) + "</div>"
    main = top + body[m.end():] + book(meta, url)
    # Ne jamais couper « Enghien-les-Bains » en fin de ligne dans un titre
    main = re.sub(r"<h([123])([^>]*)>(.*?)</h\1>",
                  lambda m: f'<h{m[1]}{m[2]}>' + m[3].replace("Enghien-les-Bains", '<span class="nw">Enghien-les-Bains</span>') + f'</h{m[1]}>',
                  main, flags=re.S)
    page = (
        head(meta, css) + "\n<body>\n" + header(meta.get("nav")) + "\n"
        f'<main id="main">{main}</main>\n' + footer(year) + "\n</body>\n</html>\n"
    )
    leftovers = re.findall(r"\{\{[^}]*\}\}", page)
    if leftovers:
        raise SystemExit(f"{slug}: marqueurs non remplacés {leftovers}")
    return page


def output_path(slug: str) -> Path:
    if slug == "index":
        return ROOT / "index.html"
    if slug == "404":
        return ROOT / "404.html"
    return ROOT / slug / "index.html"


def sitemap(pages: list[tuple[str, dict]]) -> str:
    rows = []
    for slug, meta in pages:
        sm = meta.get("sitemap")
        if not sm:
            continue
        img = ""
        if sm.get("image"):
            img = (f"<image:image><image:loc>{SITE}{sm['image']}</image:loc>"
                   f"<image:title>{esc(sm['image_title'])}</image:title></image:image>")
        rows.append(f"<url><loc>{meta['canonical']}</loc><lastmod>{meta['lastmod']}</lastmod>"
                    f"<changefreq>{sm['changefreq']}</changefreq><priority>{sm['priority']}</priority>{img}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "\n".join(rows) + "\n</urlset>\n")


def main() -> int:
    check = "--check" in sys.argv
    css = minify_css((SRC / "site.css").read_text(encoding="utf-8"))
    pages = []
    for d in sorted((SRC / "pages").iterdir()):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        pages.append((d.name, meta))
    year = max(int(m["lastmod"][:4]) for _, m in pages if m.get("lastmod"))
    outputs = {output_path(slug): render(slug, meta, (SRC / "pages" / slug / "body.part").read_text(encoding="utf-8"), css, year)
               for slug, meta in pages}
    outputs[ROOT / "sitemap.xml"] = sitemap(pages)
    stale = []
    for path, content in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            stale.append(path.relative_to(ROOT))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    if check:
        if stale:
            print("Pages non régénérées :", ", ".join(map(str, stale)))
            print("Lancer : python3 scripts/build.py")
            return 1
        print(f"Build à jour ({len(outputs)} fichiers)")
        return 0
    print(f"{len(outputs)} fichiers générés, {len(stale)} modifiés (CSS inline : {len(css)} octets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
