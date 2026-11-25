# drelard.com

Site professionnel du Dr Stéphane Elard, chirurgien urologue, publié par GitHub Pages depuis la branche `main`.

## Modifier le site

Les pages HTML à la racine sont **générées** : ne pas les modifier à la main.

1. Modifier la source dans `_src/` :
   - `_src/site.css` : la feuille de style unique (inlinée dans chaque page) ;
   - `_src/pages/<page>/body.part` : le contenu de la page ;
   - `_src/pages/<page>/meta.json` : titre, description, données sociales, JSON-LD, fil d’Ariane, bloc de rendez-vous, date `lastmod`.
2. Régénérer : `python3 scripts/build.py` (met aussi à jour `sitemap.xml`).
3. Vérifier : `python3 scripts/site_audit.py`.

L’intégration continue refuse une modification si les pages ne correspondent pas aux sources (`scripts/build.py --check`), puis lance l’audit HTML/SEO et Lighthouse.

## Choix techniques

- Aucun JavaScript exécuté : menu mobile en `<details>`, navigation instantanée par `speculationrules`.
- CSS inline (≈ 13 Ko, ≈ 3,5 Ko compressé), aucune requête bloquante.
- Une seule photo, en AVIF/WebP/JPEG responsive (`assets/img/`).
- Police Atkinson Hyperlegible Next auto-hébergée (18 Ko, sous-ensemble latin, `font-display: optional`), licence dans `assets/fonts/OFL.txt`.
