---
description: "Fige l'état d'un chantier dans un fichier court pour repartir proprement dans une nouvelle conversation. Utiliser quand l'utilisateur dit « fais une passation », « passe le relais », « on change de chantier », « note où on en est ». Pour reprendre, utiliser /reprise."
---
# /passation : passer le relais

Une conversation très longue coûte cher et se brouille. Ce geste fige l'état d'un chantier pour qu'une conversation neuve reparte sans rien réexpliquer.

Écris `outputs/passation/AAAA-MM-JJ-<chantier>.md` (dates absolues, jamais « hier ») avec :

1. **Mission** : le but du chantier en une phrase, et le critère « fini ».
2. **Décisions prises** : ce qui est tranché, avec qui l'a tranché (l'utilisateur ou toi). Ne plus le rediscuter.
3. **Fait** : ce qui est terminé ET vérifié (avec la preuve : commande, fichier, test).
4. **En cours** : ce qui est commencé, où ça s'est arrêté exactement.
5. **Prochaines actions** : dans l'ordre, la première en premier, avec qui la fait (toi ou elle) et le temps.
6. **Pièges** : ce qui a cassé, ce qu'il ne faut pas refaire.
7. **Fichiers** : les chemins utiles, en liens.

Puis : une entrée dans `log.md`, mise à jour des tâches touchées, mise à jour de `wiki/maps/parcours.md` si c'est une étape du parcours.

Réponds avec le chemin du fichier et une ligne à coller dans la nouvelle conversation : « /reprise ».
