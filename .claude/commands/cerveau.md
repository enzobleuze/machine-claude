---
description: "Interroge le vault par le sens (pas seulement le mot-clé) et montre les meilleures notes avec leur chemin. Utiliser quand l'utilisateur dit « cherche dans mes notes », « qu'est-ce que j'ai déjà sur X », « /cerveau »."
---
# /cerveau : chercher par le sens

Lance :

```bash
python scripts/cerveau.py "$ARGUMENTS"
```

Puis lance 2 reformulations par le sens (synonymes, émotion, situation) et fusionne. Présente les résultats groupés en VÉCU / PRINCIPES / SOURCES selon le dossier de chaque note, avec son chemin. Nomme l'étagère vide. Termine par le mode utilisé (sens ou mots-clés).
