#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
INFORMATION_PAGES = frozenset(f'{name}/index.html' for name in (
    'incontinence-urinaire', 'infections-urinaires', 'sang-dans-les-urines',
    'troubles-erection', 'infertilite-masculine', 'vasectomie',
    'cystoscopie-bilan-urodynamique', 'chirurgie-robot-assistee',
))
VOID_ELEMENTS = frozenset(('area', 'base', 'br', 'col', 'embed', 'hr', 'img',
                           'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'))

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags=[]; self.attrs=[]; self.ids=[]; self.links=[]; self.images=[]; self.h1=0; self.lang=None; self.title=''; self.in_title=False; self.jsonld=[]; self.in_jsonld=False; self.buf=[]
        self.link_texts=[]; self.element_stack=[]; self.link_index=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs); self.tags.append(tag); self.attrs.append((tag,a))
        hidden = (bool(self.element_stack and self.element_stack[-1][1])
                  or 'hidden' in a or (a.get('aria-hidden') or '').lower() == 'true'
                  or tag in ('script', 'style'))
        if tag not in VOID_ELEMENTS: self.element_stack.append((tag, hidden))
        if tag=='html': self.lang=a.get('lang')
        if tag=='h1': self.h1+=1
        if 'id' in a: self.ids.append(a['id'])
        if tag=='a':
            self.link_index=len(self.links); self.links.append(a); self.link_texts.append('')
        if tag=='br' and self.link_index is not None and not hidden:
            self.link_texts[self.link_index] += ' '
        if tag=='img': self.images.append(a)
        if tag=='title': self.in_title=True
        if tag=='script' and a.get('type')=='application/ld+json': self.in_jsonld=True; self.buf=[]
    def handle_endtag(self, tag):
        if tag=='a': self.link_index=None
        for i in range(len(self.element_stack) - 1, -1, -1):
            if self.element_stack[i][0] == tag:
                del self.element_stack[i:]
                break
        if tag=='title': self.in_title=False
        if tag=='script' and self.in_jsonld:
            self.in_jsonld=False; self.jsonld.append(''.join(self.buf)); self.buf=[]
    def handle_data(self,data):
        if self.in_title: self.title += data
        if self.in_jsonld: self.buf.append(data)
        if self.link_index is not None and not (self.element_stack and self.element_stack[-1][1]):
            self.link_texts[self.link_index] += data

def external_link_label_errors(parser, prefix):
    """Keep each visible link label in its explicitly overridden accessible name."""
    errors=[]
    for link, visible_text in zip(parser.links, parser.link_texts):
        url=urlparse(link.get('href', ''))
        external = (url.scheme in ('http', 'https') or bool(url.netloc)) and url.hostname not in ('drelard.com', 'www.drelard.com')
        if not external or (link.get('target') or '').lower() != '_blank' or 'aria-label' not in link:
            continue
        visible_label=' '.join(visible_text.split()).casefold()
        accessible_label=' '.join((link['aria-label'] or '').split()).casefold()
        if visible_label and visible_label not in accessible_label:
            errors.append(f'{prefix}: aria-label masque le libellé visible "{visible_text.strip()}": {link.get("href", "")}')
    return errors

def local_target(href):
    if not href or href.startswith(('#','tel:','mailto:','javascript:','data:')): return None
    u=urlparse(href)
    if u.scheme in ('http','https'):
        if u.netloc not in ('drelard.com','www.drelard.com'): return None
    path=unquote(u.path or '/')
    if path.endswith('/'): path += 'index.html'
    elif not Path(path).suffix: path += '/index.html'
    return ROOT / path.lstrip('/')

def main():
    ERRORS=[]; WARNINGS=[]
    for file in sorted(ROOT.rglob('*.html')):
        if '/.github/' in str(file) or '/.restore' in str(file): continue
        rel=file.relative_to(ROOT)
        text=file.read_text(encoding='utf-8')

        if rel.parent == Path('.') and re.fullmatch(r'google[a-zA-Z0-9_-]+\.html', rel.name):
            expected = f'google-site-verification: {rel.name}'
            if text.strip() != expected:
                ERRORS.append(f'{rel}: contenu de vérification Google invalide')
            continue

        p=Parser(); p.feed(text)
        prefix=str(rel)
        if rel.as_posix() in INFORMATION_PAGES:
            ERRORS.extend(external_link_label_errors(p, prefix))
        if p.lang!='fr': ERRORS.append(f'{prefix}: attribut lang="fr" absent')
        if not p.title.strip(): ERRORS.append(f'{prefix}: title absent')
        if p.h1!=1: ERRORS.append(f'{prefix}: {p.h1} balise(s) h1, attendu 1')
        for tag in ('main','nav','footer'):
            if tag not in p.tags: ERRORS.append(f'{prefix}: repère sémantique <{tag}> absent')
        if len(p.ids)!=len(set(p.ids)): ERRORS.append(f'{prefix}: identifiants HTML dupliqués')
        if 'meta name="description"' not in text: ERRORS.append(f'{prefix}: meta description absente')
        noindex = bool(re.search(r'<meta name="robots" content="[^"]*noindex', text))
        if not noindex and 'rel="canonical"' not in text: ERRORS.append(f'{prefix}: URL canonique absente')
        if noindex and 'rel="canonical"' in text: WARNINGS.append(f'{prefix}: page noindex avec URL canonique')
        if str(rel) == '404.html' and not noindex: ERRORS.append('404.html: doit être en noindex')
        if not noindex:
            m = re.search(r'name="description" content="([^"]*)"', text)
            if m and len(m.group(1)) > 170: WARNINGS.append(f'{prefix}: meta description trop longue ({len(m.group(1))} car.)')
            if len(p.title.strip()) > 65: WARNINGS.append(f'{prefix}: title trop long ({len(p.title.strip())} car.)')
            for tag in ('og:title','og:description','og:image','og:url','twitter:card'):
                if f'"{tag}"' not in text: WARNINGS.append(f'{prefix}: balise {tag} absente')
        if 'focus-visible' not in text: ERRORS.append(f'{prefix}: style de focus visible absent')
        if 'prefers-reduced-motion' not in text: ERRORS.append(f'{prefix}: réduction des animations absente')
        if 'Aller au contenu' not in text: WARNINGS.append(f'{prefix}: lien d’évitement non détecté')
        for img in p.images:
            if not img.get('alt') and img.get('role')!='presentation': ERRORS.append(f'{prefix}: image sans texte alternatif')
            if not img.get('width') or not img.get('height'): WARNINGS.append(f'{prefix}: image sans dimensions explicites')
        for link in p.links:
            href=link.get('href','')
            if link.get('target')=='_blank' and 'noopener' not in link.get('rel',''): ERRORS.append(f'{prefix}: lien target=_blank sans noopener: {href}')
            target=local_target(href)
            if target and not target.exists(): ERRORS.append(f'{prefix}: cible locale absente: {href}')
            if href=='#': WARNINGS.append(f'{prefix}: lien vide href="#"')
        for raw in p.jsonld:
            try: json.loads(raw)
            except Exception as exc: ERRORS.append(f'{prefix}: JSON-LD invalide: {exc}')

    for required in ('llms.txt','sitemap.xml','robots.txt','site.webmanifest','urologue-enghien-les-bains/index.html','rendez-vous/index.html','incontinence-urinaire/index.html','infections-urinaires/index.html','sang-dans-les-urines/index.html','troubles-erection/index.html','infertilite-masculine/index.html','vasectomie/index.html','cystoscopie-bilan-urodynamique/index.html','chirurgie-robot-assistee/index.html','plan-du-site/index.html','accessibilite/index.html'):
        if not (ROOT/required).exists(): ERRORS.append(f'Fichier requis absent: {required}')

    index=(ROOT/'index.html').read_text(encoding='utf-8')
    for required in ('tel:+33130756301','tel:+33139641494','potentialAction','/urologue-enghien-les-bains/','/prolapsus-genital/','/rendez-vous/'):
        if required not in index: ERRORS.append(f'Accueil: donnée agentique absente: {required}')

    enghien_path=ROOT/'urologue-enghien-les-bains/index.html'
    if enghien_path.exists():
        enghien=enghien_path.read_text(encoding='utf-8')
        for required in ('Urologue à Enghien-les-Bains','8 rue de Malleville','tel:+33139641494','FAQPage','Physician'):
            if required not in enghien: ERRORS.append(f'Page Enghien: donnée locale absente: {required}')
        if 'Review' in enghien or 'AggregateRating' in enghien:
            ERRORS.append('Page Enghien: balisage de notation interdit par la politique éditoriale')

    print(f'Audit: {len(ERRORS)} erreur(s), {len(WARNINGS)} avertissement(s)')
    for x in WARNINGS: print('WARN',x)
    for x in ERRORS: print('ERROR',x)
    return 1 if ERRORS else 0


if __name__ == '__main__':
    sys.exit(main())
