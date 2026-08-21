# dieppeoratoriens.com — préparation GitHub Pages

Cette branche isolée contient le paquet de déploiement du site officiel **ORATORIENS HENRI IV — Dieppe**.

## Sécurité

- Les URL iCal privées Booking.com et Airbnb ne sont jamais enregistrées dans le dépôt.
- Elles doivent être ajoutées dans les secrets GitHub Actions `BOOKING_ICAL_URL` et `AIRBNB_ICAL_URL`.
- Le workflow transforme les calendriers en simples périodes occupées, sans nom de voyageur ni détail de réservation.

## Publication prévue

Le contenu doit être publié dans un dépôt séparé nommé `stephanelard-cmd/dieppeoratoriens.com`, branche `main`. Il ne faut pas fusionner cette branche dans la branche `main` du dépôt médical `drelard.com`.

Dans le nouveau dépôt :

1. Ajouter les deux secrets Actions.
2. Choisir **GitHub Actions** comme source GitHub Pages.
3. Utiliser `dieppeoratoriens.com` comme domaine personnalisé.
4. Configurer les DNS chez OVHcloud.

La synchronisation des disponibilités est planifiée toutes les trois heures et peut aussi être déclenchée manuellement.
