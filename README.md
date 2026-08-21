# Staging — dieppeoratoriens.com

Cette branche contient le paquet prêt à transférer dans un **dépôt GitHub dédié** nommé `dieppeoratoriens.com`.

Ne pas fusionner cette branche dans `main` du dépôt `drelard.com` : ce dépôt héberge déjà le site médical et GitHub Pages ne publie qu’un site par dépôt.

## Contenu prêt

- domaine `dieppeoratoriens.com` via `CNAME` ;
- site statique GitHub Pages ;
- synchronisation Booking.com et Airbnb programmée toutes les 15 minutes ;
- échec fermé : aucun nouveau déploiement si un flux iCal ne répond pas ;
- URL iCal attendues dans les secrets `BOOKING_ICAL_URL` et `AIRBNB_ICAL_URL` ;
- données du logement corrigées d’après l’inspection et la décision ADTER de 2019 ;
- distinction explicite entre l’annonce actuelle jusqu’à 5 voyageurs et l’ancien classement 2 étoiles pour 4 personnes, expiré le 31 octobre 2024 ;
- aucune coordonnée personnelle issue des PDF n’est publiée.

Le paquet source est découpé dans `package/site.zip.b64.*` et vérifié par SHA-256 avant chaque déploiement.
