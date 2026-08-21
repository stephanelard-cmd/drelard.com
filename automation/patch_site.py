#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else 'source').resolve()
SCHEMA={"@context":"https://schema.org","@type":"VacationRental","name":"Oratoriens Henri IV","description":"Studio-mezzanine face au port de Dieppe, proposé pour un maximum de 5 voyageurs sur les plateformes de réservation.","url":"https://dieppeoratoriens.com/","image":"https://dieppeoratoriens.com/assets/images/hero.webp","identifier":"76217000744E2","address":{"@type":"PostalAddress","streetAddress":"31–33 quai Henri IV","postalCode":"76200","addressLocality":"Dieppe","addressCountry":"FR"},"geo":{"@type":"GeoCoordinates","latitude":49.928033,"longitude":1.080668},"numberOfRooms":1,"floorSize":{"@type":"QuantitativeValue","value":35,"unitCode":"MTK"},"occupancy":{"@type":"QuantitativeValue","maxValue":5},"checkinTime":"15:00","checkoutTime":"11:00","petsAllowed":True,"amenityFeature":[{"@type":"LocationFeatureSpecification","name":"Wi-Fi haut débit","value":True},{"@type":"LocationFeatureSpecification","name":"Cuisine équipée","value":True},{"@type":"LocationFeatureSpecification","name":"Lave-linge","value":True},{"@type":"LocationFeatureSpecification","name":"Sèche-linge","value":True},{"@type":"LocationFeatureSpecification","name":"Système de rafraîchissement d’air","value":True},{"@type":"LocationFeatureSpecification","name":"Parking public à proximité","value":True},{"@type":"LocationFeatureSpecification","name":"Parking privé","value":False},{"@type":"LocationFeatureSpecification","name":"Lave-vaisselle","value":False}]}

def load(name): return BeautifulSoup((ROOT/name).read_text(encoding='utf-8'),'html.parser')
def save(name,soup): (ROOT/name).write_text(str(soup),encoding='utf-8')
def meta(soup,title=None,desc=None,url=None):
    if title:
        if soup.title:soup.title.string=title
        x=soup.find('meta',attrs={'property':'og:title'}); x and x.__setitem__('content',title)
    if desc:
        x=soup.find('meta',attrs={'name':'description'}); x and x.__setitem__('content',desc)
        x=soup.find('meta',attrs={'property':'og:description'}); x and x.__setitem__('content',desc)
    if url:
        x=soup.find('link',rel='canonical'); x and x.__setitem__('href',url)
        x=soup.find('meta',attrs={'property':'og:url'}); x and x.__setitem__('content',url)
def setmain(name,html):
    s=load(name); old=s.find('main',id='contenu'); new=BeautifulSoup(html,'html.parser').find('main')
    if old and new:old.replace_with(new)
    save(name,s)

for p in ROOT.rglob('*.html'):
    s=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    x=s.find('script',attrs={'type':'application/ld+json'})
    if x:x.string=json.dumps(SCHEMA,ensure_ascii=False,separators=(',',':'))
    x=s.select_one('.topbar')
    if x:x.string='Harbour mezzanine studio · up to 5 guests · explore Dieppe on foot' if '/en/' in p.as_posix() else 'Studio-mezzanine face au port · jusqu’à 5 voyageurs · Dieppe à pied'
    for d in s.select('.footer-grid > div'):
        st=d.find('strong')
        if st and st.get_text(strip=True)=='Informations':
            q=d.find('p')
            if q and not q.find('a',href='/classement-equipements.html'):
                q.append(s.new_tag('br')); a=s.new_tag('a',href='/classement-equipements.html');a.string='Classement & équipements';q.append(a)
    p.write_text(str(s),encoding='utf-8')

s=load('index.html');meta(s,'Oratoriens Henri IV | Studio-mezzanine face au port de Dieppe','Studio-mezzanine d’environ 35 m² pour jusqu’à 5 voyageurs, face au port de Dieppe, à proximité de la plage, du marché et des restaurants.')
x=s.select_one('.hero-content p'); x and setattr(x,'string','Un studio-mezzanine d’environ 35 m² dans un immeuble historique du quai Henri IV, proposé pour accueillir jusqu’à cinq voyageurs.')
for f,v in zip(s.select('.quick-grid .fact'),[('≈ 35 m²','27 m² habitables hors salle d’eau et WC mesurés en 2019'),('5 voyageurs','capacité affichée sur les plateformes'),('Vue port','quai Henri IV, exposition plein sud'),('Tout à pied','plage, marché, restaurants et commerces')]):
    a,b=f.find('strong'),f.find('span');
    if a:a.string=v[0]
    if b:b.string=v[1]
ul=s.select_one('.feature-list')
if ul:
    ul.clear()
    for t in ['Wi-Fi haut débit','Cuisine équipée avec four','Lave-linge et sèche-linge','Système de rafraîchissement d’air','Arrivée autonome','Animaux admis']:
        li=s.new_tag('li');li.string=t;ul.append(li)
card=s.select_one('.two .card')
if card:
    ps=card.find_all('p')
    if ps:ps[0].string='Trois lits simples sur la mezzanine et un canapé convertible 140 × 190 dans le séjour. La capacité affichée sur Airbnb est de cinq voyageurs.'
    if len(ps)>1:
        ps[1].clear();ps[1].append('Le classement 2 étoiles attribué en 2019 portait sur quatre personnes et a expiré le 31 octobre 2024. ');a=s.new_tag('a',href='/classement-equipements.html');a.string='Voir les données de contrôle.';ps[1].append(a)
for c in s.select('.section-alt .card'):
    h=c.find('h3')
    if h and h.get_text(strip=True)=='Autonome':
        p=c.find('p'); p and setattr(p,'string','Four, mini-four, micro-ondes, plaques vitrocéramiques ou à induction, hotte, réfrigérateur, cafetière, bouilloire et grille-pain.')
h=s.find('h2',string=lambda z:z and 'calendriers synchronisés' in z)
if h:
    p=h.find_next('p'); p and setattr(p,'string','Les périodes occupées de Booking.com et Airbnb sont réunies dans un calendrier dont l’actualisation est programmée toutes les quinze minutes.')
save('index.html',s)

setmain('hebergement.html','''<main id="contenu"><section class="page-hero"><div class="wrap"><div class="breadcrumbs"><a href="/">Accueil</a> / Le logement</div><div class="eyebrow">Studio-mezzanine face au port</div><h1>Un espace de caractère, compact et bien équipé</h1><p class="lead">Environ 35 m² annoncés sur les plateformes, dont 27 m² habitables hors salle d’eau et toilettes relevés lors de l’inspection de 2019.</p></div></section><section class="section"><div class="wrap"><div class="card-grid"><article class="card"><div class="icon">🛏️</div><h3>Couchages</h3><p>Trois lits simples de 90 × 190 cm sur la mezzanine et un canapé convertible de 140 × 190 cm dans le séjour. L’annonce actuelle accepte jusqu’à cinq voyageurs.</p></article><article class="card"><div class="icon">🍽️</div><h3>Cuisine complète</h3><p>Four, mini-four, micro-ondes, plaques vitrocéramiques ou à induction, hotte, réfrigérateur, cafetière, bouilloire, grille-pain, vaisselle et matériel de préparation.</p></article><article class="card"><div class="icon">🚿</div><h3>Salle d’eau</h3><p>Douche, lavabo avec eau chaude, toilettes, miroir, rangements, patères et sèche-cheveux.</p></article><article class="card"><div class="icon">🧺</div><h3>Entretien du linge</h3><p>Lave-linge et sèche-linge électrique contrôlés lors de la visite de classement.</p></article><article class="card"><div class="icon">📶</div><h3>Connexion & loisirs</h3><p>Wi-Fi haut débit, télévision à écran plat, chaînes internationales ou thématiques, chaîne hi-fi et lecteur DVD constatés en 2019.</p></article><article class="card"><div class="icon">🌡️</div><h3>Confort thermique</h3><p>Chauffage et système de climatisation ou de rafraîchissement d’air validés lors de l’inspection.</p></article></div></div></section><section class="section section-alt"><div class="wrap two"><div><div class="eyebrow">À savoir avant de réserver</div><h2>Les informations utiles, sans mauvaise surprise</h2><ul class="feature-list"><li>Pas de stationnement privé sur place</li><li>Parkings publics à proximité</li><li>Pas de lave-vaisselle</li><li>Pas de congélateur séparé</li><li>Pas de balcon, terrasse ou jardin</li><li>Pas de matériel bébé garanti</li></ul><p class="notice">Le logement se rejoint uniquement par des escaliers et n’est pas présenté comme accessible aux personnes à mobilité réduite. La mezzanine a une hauteur inférieure à 1,65 m.</p></div><div class="card"><div class="eyebrow">Données documentées</div><h3>Inspection ADTER du 28 octobre 2019</h3><p>La visite a validé 153 points obligatoires sur 160 et 79 points à la carte. Le classement 2 étoiles accordé le 31 octobre 2019 concernait quatre personnes et était valable cinq ans.</p><p><strong>Ce classement a expiré le 31 octobre 2024.</strong> Le site ne revendique donc aucun classement étoilé actuellement en cours.</p><a class="btn btn-primary" href="/classement-equipements.html">Consulter le détail</a></div></div></section><section class="section"><div class="wrap"><div class="eyebrow">Réserver</div><h2>Vérifiez les équipements contractuels sur la plateforme choisie</h2><p class="lead">Les équipements peuvent évoluer depuis l’inspection de 2019. La fiche Booking.com ou Airbnb au moment de la réservation reste la référence contractuelle.</p><div class="actions"><a class="btn btn-primary" href="/disponibilites.html">Voir les disponibilités</a><a class="btn btn-outline" href="https://www.booking.com/hotel/fr/oratoriens-henri-iv.fr.html" rel="external nofollow">Booking.com</a><a class="btn btn-outline" href="https://www.airbnb.fr/rooms/992531447842701708" rel="external nofollow">Airbnb</a></div></div></section></main>''')
setmain('informations.html','''<main id="contenu"><section class="page-hero"><div class="wrap"><div class="breadcrumbs"><a href="/">Accueil</a> / Informations</div><div class="eyebrow">Préparer votre arrivée</div><h1>Informations pratiques</h1><p class="lead">Horaires, accès, stationnement, sécurité et règles essentielles du séjour.</p></div></section><section class="section"><div class="wrap legal"><h2>Arrivée et départ</h2><p>Arrivée entre 15 h et minuit et départ avant 11 h. L’arrivée autonome s’effectue par serrure à digicode. Communiquez votre horaire prévisionnel via la plateforme de réservation.</p><h2>Capacité et couchages</h2><p>L’annonce actuelle accepte jusqu’à cinq voyageurs et présente trois lits simples ainsi qu’un canapé convertible. Le classement historique de 2019 avait été délivré pour quatre personnes.</p><h2>Stationnement</h2><p>Il n’existe pas de place de stationnement privée sur place. Des emplacements sur voirie et des parkings publics sont disponibles à proximité du port.</p><h2>Animaux</h2><p>Les animaux sont admis sous réserve des conditions et éventuels frais affichés lors de la réservation.</p><h2>Vie dans l’immeuble</h2><p>Pas de fête ni d’événement. Respect du calme entre 22 h et 9 h. Le logement est entièrement non-fumeur.</p><h2>Accessibilité</h2><p>Accès uniquement par des escaliers, sans équipement d’accessibilité spécifique validé. La mezzanine présente une hauteur inférieure à 1,65 m.</p><h2>Sécurité</h2><p>Un détecteur de fumée est présent. L’annonce Airbnb indique qu’aucun détecteur de monoxyde de carbone n’est disponible.</p><h2>Équipements non disponibles ou non garantis</h2><p>Pas de lave-vaisselle, de congélateur séparé, de parking privé, de balcon, de terrasse, de jardin ni de matériel bébé garanti.</p><h2>Actualisation des informations</h2><p>Les équipements et conditions peuvent évoluer. Les informations affichées sur Booking.com ou Airbnb au moment de la réservation prévalent.</p></div></section></main>''')

s=load('disponibilites.html');x=s.select_one('.page-hero .lead'); x and setattr(x,'string','Les dates déjà occupées sur Booking.com ou Airbnb sont réunies ci-dessous. Une actualisation automatique est programmée toutes les quinze minutes.');x=s.select_one('.calendar-info small');x and setattr(x,'string','Une date sans blocage reste à confirmer sur la plateforme avant paiement. Un léger décalage de synchronisation reste possible.');save('disponibilites.html',s)
s=load('avis-localisation.html');P=s.select('.platform')
if len(P)>1:
    x=P[0].select_one('.rating');x and setattr(x,'string','8,4 / 10');x=P[0].find('p');x and setattr(x,'string','Note constatée le 21 août 2026 sur Booking.com. Consultez la plateforme pour la note et le nombre d’avis en temps réel.');x=P[1].select_one('.rating');x and setattr(x,'string','4,75 / 5');x=P[1].find('p');x and setattr(x,'string','Note constatée le 21 août 2026 sur Airbnb, sur la base de quatre commentaires. Consultez la plateforme pour les données en temps réel.')
x=s.select_one('.notice');x and setattr(x,'string','Ces évaluations proviennent exclusivement de Booking.com et Airbnb. Elles ne sont pas présentées comme des avis Google et aucun avis n’est collecté directement par ce site.');save('avis-localisation.html',s)

s=load('en/index.html');meta(s,'Oratoriens Henri IV | Dieppe harbour mezzanine studio','Approximately 35 m² mezzanine studio for up to five guests on Dieppe harbour, close to the beach, restaurants and town centre.');x=s.select_one('.page-hero .lead');x and setattr(x,'string','Approximately 35 m² for up to five guests, including 27 m² of living space excluding the shower room and WC measured during the 2019 inspection. Equipped kitchen, Wi-Fi and harbour views.');save('en/index.html',s)

s=load('mentions-legales.html');q=s.select_one('.legal')
if q and not q.find(string=lambda z:z and 'expiré le 31 octobre 2024' in z):
    h=s.new_tag('h2');h.string='Classement et informations historiques';q.append(h);p=s.new_tag('p');p.string='Le classement 2 étoiles délivré le 31 octobre 2019 pour quatre personnes était valable cinq ans et a expiré le 31 octobre 2024. Le site ne revendique pas de classement étoilé en cours.';q.append(p)
save('mentions-legales.html',s)

base=load('informations.html');meta(base,'Classement et équipements | Oratoriens Henri IV Dieppe','Données vérifiées de l’inspection 2019, historique du classement et principaux équipements du studio-mezzanine Oratoriens Henri IV.','https://dieppeoratoriens.com/classement-equipements.html')
main=BeautifulSoup('''<main id="contenu"><section class="page-hero"><div class="wrap"><div class="breadcrumbs"><a href="/">Accueil</a> / Classement & équipements</div><div class="eyebrow">Données documentées</div><h1>Classement historique et équipements contrôlés</h1><p class="lead">Synthèse publique des éléments utiles des documents ADTER de 2019, sans diffusion des coordonnées personnelles figurant dans les pièces originales.</p></div></section><section class="section"><div class="wrap"><div class="card-grid"><article class="card"><div class="eyebrow">Inspection</div><h3>28 octobre 2019</h3><p>Visite réalisée par ADTER Seine-Maritime.</p></article><article class="card"><div class="eyebrow">Décision</div><h3>2 étoiles</h3><p>Classement accordé le 31 octobre 2019 pour une capacité de quatre personnes.</p></article><article class="card"><div class="eyebrow">Échéance</div><h3>31 octobre 2024</h3><p>La décision indiquait une validité de cinq ans. Elle n’est donc plus en cours.</p></article></div><p class="notice"><strong>Aucune étoile actuelle n’est revendiquée sur ce site.</strong> L’annonce commerciale actuelle des plateformes accepte jusqu’à cinq voyageurs ; cela est distinct de l’ancien classement délivré pour quatre personnes.</p></div></section><section class="section section-alt"><div class="wrap"><div class="eyebrow">Surface et résultat</div><h2>Mesures et seuils de l’inspection</h2><div class="card-grid"><article class="card"><h3>27 m²</h3><p>Surface habitable relevée, cuisine comprise, hors salle d’eau et toilettes.</p></article><article class="card"><h3>153 / 160</h3><p>Points obligatoires atteints, soit 95,63 %, avec seuil respecté.</p></article><article class="card"><h3>79 points</h3><p>Points à la carte atteints pour un seuil requis de 34,3 points.</p></article></div></div></section><section class="section"><div class="wrap two"><div><div class="eyebrow">Équipements validés en 2019</div><h2>Confort, cuisine et services</h2><ul class="feature-list"><li>Wi-Fi haut débit</li><li>Télévision à écran plat</li><li>Chaînes internationales ou thématiques</li><li>Chaîne hi-fi et lecteur DVD</li><li>Chauffage</li><li>Climatisation ou rafraîchissement d’air</li><li>Lave-linge</li><li>Sèche-linge électrique</li><li>Four, mini-four et micro-ondes</li><li>Plaques vitrocéramiques ou à induction</li><li>Hotte ou ventilation</li><li>Cafetière, bouilloire et grille-pain</li><li>Réfrigérateur avec compartiment conservateur</li><li>Sèche-cheveux</li><li>Vue paysagère sur le port</li><li>Accès immédiat à la plage ou au plan d’eau</li></ul></div><div class="card"><div class="eyebrow">Limitations constatées</div><h3>Éléments non validés</h3><ul><li>Pas de place de stationnement privée ni garage</li><li>Pas de balcon, terrasse ou jardin</li><li>Pas de lave-vaisselle</li><li>Pas de congélateur séparé</li><li>Pas de matériel bébé</li><li>Portes et équipements d’accessibilité non adaptés</li></ul><p>Des emplacements publics à proximité avaient en revanche été validés.</p></div></div></section><section class="section section-alt"><div class="wrap"><div class="eyebrow">Environnement</div><h2>Mesures responsables validées</h2><p class="lead">Réduction des consommations d’énergie et d’eau, tri sélectif, information des voyageurs et utilisation de produits d’entretien respectueux de l’environnement figuraient parmi les critères validés.</p><p class="notice">Cette page décrit l’état constaté en 2019. Les fiches Booking.com et Airbnb au moment de la réservation restent la référence pour les équipements actuellement proposés.</p></div></section></main>''','html.parser').find('main');base.find('main',id='contenu').replace_with(main);save('classement-equipements.html',base)

sm=ROOT/'sitemap.xml'
if sm.exists():
    t=sm.read_text(encoding='utf-8').replace('<url><loc>https://dieppeoratoriens.com/disponibilites.html</loc><changefreq>weekly</changefreq></url>','<url><loc>https://dieppeoratoriens.com/disponibilites.html</loc><changefreq>daily</changefreq></url>')
    e='<url><loc>https://dieppeoratoriens.com/classement-equipements.html</loc><changefreq>yearly</changefreq></url>\n'
    if e not in t:t=t.replace('</urlset>',e+'</urlset>')
    sm.write_text(t,encoding='utf-8')
js=ROOT/'assets/js/calendar.js'
if js.exists():
    t=js.read_text(encoding='utf-8').replace("Calendriers mis à jour le ${new Date(state.fresh).toLocaleString('fr-FR')}.","Calendriers mis à jour le ${new Date(state.fresh).toLocaleString('fr-FR')}. Actualisation programmée toutes les 15 minutes.")
    js.write_text(t,encoding='utf-8')
print('patched',ROOT)
