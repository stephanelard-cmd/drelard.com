#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
ERRORS=[]; WARNINGS=[]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags=[]; self.attrs=[]; self.ids=[]; self.links=[]; self.images=[]; self.h1=0; self.lang=None; self.title=''; self.in_title=False; self.jsonld=[]; self.in_jsonld=False; self.buf=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs); self.tags.append(tag); self.attrs.append((tag,a))
        if tag=='html': self.lang=a.get('lang')
        if tag=='h1': self.h1+=1
        if 'id' in a: self.ids.append(a['id'])
        if tag=='a': self.links.append(a)
        if tag=='img': self.images.append(a)
        if tag=='title': self.in_title=True
        if tag=='script' and a.get('type')=='application/ld+json': self.in_jsonld=True; self.buf=[]
    def handle_endtag(self, tag):
        if tag=='title': self.in_title=False
        if tag=='script' and self.in_jsonld:
            self.in_jsonld=False; self.jsonld.append(''.join(self.buf)); self.buf=[]
    def handle_data(self,data):
        if self.in_title: self.title += data
        if self.in_jsonld: self.buf.append(data)

def local_target(href):
    if not href or href.startswith(('#','tel:','mailto:','javascript:','data:')): return None
    u=urlparse(href)
    if u.scheme in ('http','https'):
        if u.netloc not in ('drelard.com','www.drelard.com'): return None
    path=unquote(u.path or '/')
    if path.endswith('/'): path += 'index.html'
    elif not Path(path).suffix: path += '/index.html'
    return ROOT / path.lstrip('/')

for file in sorted(ROOT.rglob('*.html')):
    if '/.github/' in str(file) or '/.restore' in str(file): continue
    rel=file.relative_to(ROOT)
    text=file.read_text(encoding='utf-8')
    p=Parser(); p.feed(text)
    prefix=str(rel)
    if p.lang!='fr': ERRORS.append(f'{prefix}: attribut lang="fr" absent')
    if not p.title.strip(): ERRORS.append(f'{prefix}: title absent')
    if p.h1!=1: ERRORS.append(f'{prefix}: {p.h1} balise(s) h1, attendu 1')
    for tag in ('main','nav','footer'):
        if tag not in p.tags: ERRORS.append(f'{prefix}: repère sémantique <{tag}> absent')
    if len(p.ids)!=len(set(p.ids)): ERRORS.append(f'{prefix}: identifiants HTML dupliqués')
    if 'meta name="description"' not in text: ERRORS.append(f'{prefix}: meta description absente')
    if 'rel="canonical"' not in text: ERRORS.append(f'{prefix}: URL canonique absente')
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

for required in ('llms.txt','sitemap.xml','robots.txt','site.webmanifest','rendez-vous/index.html','plan-du-site/index.html','accessibilite/index.html'):
    if not (ROOT/required).exists(): ERRORS.append(f'Fichier requis absent: {required}')
index=(ROOT/'index.html').read_text(encoding='utf-8')
for required in ('tel:+33130756301','tel:+33139641494','potentialAction','/prolapsus-genital/','/rendez-vous/'):
    if required not in index: ERRORS.append(f'Accueil: donnée agentique absente: {required}')

print(f'Audit: {len(ERRORS)} erreur(s), {len(WARNINGS)} avertissement(s)')
for x in WARNINGS: print('WARN',x)
for x in ERRORS: print('ERROR',x)
sys.exit(1 if ERRORS else 0)
