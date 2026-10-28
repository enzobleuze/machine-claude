---
name: catalogue-automatisations
description: "Présente le catalogue des automatisations possibles (sauvegardes, jardinier, ingestion nocturne, idées, publication, statistiques, relances) et choisit avec l'utilisateur la prochaine à ajouter, dans le bon ordre. Utiliser quand l'utilisateur dit « qu'est-ce que je peux automatiser », « quelle automatisation ensuite », « fais tourner plus de choses seules ». Pas pour installer une tâche déjà choisie (utiliser taches-planifiees)."
---
# Catalogue des automatisations

## Pourquoi
Le système d'origine a fini avec des dizaines de tâches planifiées. Certaines ont été créées trop tôt : elles automatisaient un travail qui n'était pas encore juste à la main, et elles ont produit des dizaines d'articles qui n'ont presque rien rapporté avant d'être mises en pause. La règle tirée de là : on automatise seulement ce qui marche déjà à la main, une brique à la fois, en commençant par ce qui protège, puis ce qui entretient, et en dernier ce qui publie.

## Prérequis
- wrapper-de-tache, taches-planifiees, gardien, notifications-telegram.
- Les briques des blocs A à E que chaque automatisation déclenche (elle les lance, elle ne les remplace pas).

## Interview
Lis d'abord : `wiki/maps/parcours.md` (ce qui est fait à la main et marche), `wiki/maps/automatisations.md`, `scripts/taches-attendues.json`, et les dernières sessions dans `log.md` (ce que l'utilisateur répète chaque semaine).
Puis demande :
1. « Qu'est-ce que tu refais toutes les semaines et qui t'ennuie ? »
2. « Qu'est-ce qui te coûterait le plus si ça disparaissait demain ? » (fixe la priorité des sauvegardes.)
3. « Combien d'heures par semaine as-tu pour le business ? » (une automatisation doit en libérer, pas en demander.)
Range les réponses et le choix final dans `wiki/maps/automatisations.md` (section « Prochaine »).

## Construire
1. **Montrer le catalogue (Claude, 5 min).** Présente ce tableau dans l'ordre d'ajout conseillé, en cochant ce qui existe déjà :

| Ordre | Automatisation | Quand | Brique qu'elle lance | Preuve pour le gardien |
|---|---|---|---|---|
| 1 | Sauvegardes (git plusieurs fois par jour, copie externe chaque nuit) | dès le jour 1 | sauvegardes-3-lieux | fichier de la dernière copie réussie |
| 2 | Gardien | dès la deuxième tâche | gardien | `outputs/gardien/{date}.json` |
| 3 | Jardinier du vault (liens, orphelins, index) | quand le vault a quelques centaines de pages | jardinier | résumé du jardinier du jour |
| 4 | Rapport du matin | dès trois tâches | rapport-du-matin | `outputs/brief-matin/{date}.md` |
| 5 | Ingestion nocturne (appels, Drive, notes, réseaux) | quand l'ingestion manuelle marche | briques d'ingestion du bloc A | nouveaux fichiers rangés |
| 6 | Scoreboard du dimanche et plan du lundi | quand le plan unique existe | scoreboard-et-plan-semaine | message parti, plan écrit |
| 7 | Idées (veille, banque d'idées classée) | quand la banque d'idées marche à la main | banque-idees, veille-et-tendances | idées ajoutées |
| 8 | Board de nuit | quand le board marche à la main | taches-de-nuit, board-textes | `outputs/nuit/{date}.md` |
| 9 | Statistiques (vues, ventes, emails) | quand une décision dépend des chiffres | mesure du bloc E, cockpit du bloc D | fichier de chiffres du jour |
| 10 | Publication programmée | seulement des textes validés | distribution du bloc E | preuve lue sur la plateforme |
| 11 | Relances (prospects, rendez-vous manqués) | quand le CRM est propre | CRM du bloc D | messages en brouillon ou envoyés |

2. **Choisir une seule prochaine (Claude, 5 min).** Avec l'utilisateur : la première ligne non cochée dont la brique marche à la main. Si elle ne marche pas encore à la main, la prochaine action est de la faire marcher à la main.
3. **Installer (Claude, 20 min).** Script de la tâche selon wrapper-de-tache (codes de sortie, contrôle du fichier produit), enregistrement selon taches-planifiees, ligne dans `taches-attendues.json`. Une seule nouvelle automatisation par semaine.
4. **Une semaine d'observation (Claude, en session).** Chaque matin, le rapport dit si elle a tourné. Au bout d'une semaine sans panne, coche-la dans le catalogue et propose la suivante.

Règles fixes pour toute automatisation :
- Idempotente : relancée deux fois, elle ne casse rien et ne publie pas deux fois.
- Déterministe d'abord : un script Python sans appel au modèle quand c'est possible ; `claude -p` seulement pour ce qui demande du jugement, et sur le modèle économique.
- Déplacer plutôt que supprimer. Un seul commit par passage pour pouvoir revenir en arrière.
- Rodage en simulation : une tâche qui écrit dans le wiki tourne d'abord en mode « plan seulement » (un fichier drapeau à la racine), puis en écriture réelle après deux passages justes.
- Publication et relance : jamais rien vers l'extérieur qui n'a pas été validé, et l'humain garde un interrupteur (`.machine-en-pause`).
- Relances envers d'anciens clients : seulement si l'utilisateur l'a dit clairement. Certains refusent, et c'est leur choix.

## Test
`wiki/maps/automatisations.md` contient le catalogue avec les cases cochées, et la prochaine automatisation choisie a une brique qui marche à la main.

## Pièges vécus
- **Automatiser une erreur** : des articles produits chaque nuit par la machine n'ont presque rien rapporté. Pause volontaire, puis retour à la qualité à la main.
- **Tout d'un coup** : plusieurs tâches ajoutées la même semaine rendent les pannes impossibles à attribuer. Une par semaine.
- **Pas de sauvegarde avant le reste** : une tâche qui écrit dans le vault sans sauvegarde peut abîmer des semaines de travail.
- **Tâche oubliée** : sans ligne au gardien, une tâche peut mourir des semaines sans bruit.
- **Rapports passifs** : un rapport que personne ne lit ne sert à rien. Le jardinier d'origine est devenu utile quand il a réparé lui-même au lieu de signaler.

## Entretien dans le temps
Le premier de chaque mois : relis le catalogue, désactive ce qui ne sert plus (`"active": false` au gardien, `-Supprimer` au planificateur), et vérifie que chaque tâche vivante a sa preuve.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Note en mémoire les automatisations refusées par l'utilisateur, pour ne plus les proposer. Propose ensuite l'automatisation choisie.
