---
name: comite-roast-ancre
description: "Mode « roast » du comité : chaque siège est un carnet NotebookLM (un expert de l'utilisateur), interrogé UNE fois avant le débat ; puis 2 ou 3 tours de débat entre sièges sans outils, cartes anonymes, notes pondérées et verdict par bandes. Utiliser quand l'utilisateur dit « roast ça », « passe ça au board des experts », « qu'en diraient mes experts ? » sur une décision à options. Pas pour juger un texte rédigé (utiliser board-textes), pas pour une décision sans carnets (utiliser comite-decision)."
---
# Le comité roast ancré sur les carnets

## Pourquoi
Le comité classique raisonne avec des angles inventés. Le roast fait parler les experts que l'utilisateur a choisis, depuis leurs propres sources. Le principe vient du système d'origine : **ancrer une fois, débattre ensuite.** Chaque siège pose une seule question à son carnet, puis les sièges débattent sans aucun accès aux fichiers, et la session préside, calcule et rend le verdict. Lancer les sièges en `claude -p` sans outils y a coûté environ dix fois moins de jetons par siège qu'un sous-agent ordinaire, qui recharge tout le contexte de Claude Code à chaque appel.

## Prérequis
- `notebooklm-brancher`, `carnets-experts`, `routage-carnets` faits.
- `comite-decision` connu (même logique de relecture anonyme).
- La commande `claude` utilisable en ligne de commande (`claude -p`, bloc B).
- Coût : annoncer avant chaque séance le nombre de sièges, de tours et de questions aux carnets.

## Interview
Lis d'abord : `carnets.json` (rôles et domaines), `wiki/maps/routage-carnets.md`, le plan du trimestre et l'index MEMORY.

À l'installation, demande :
1. « Quels types de décisions veux-tu passer au roast ? » (exemples : offre et prix, contenu, recrutement, achat d'un outil.)
2. Pour chaque type : Claude propose 4 sièges (mode rapide) et 6 ou 7 (mode complet) parmi les carnets, avec un poids de 1 à 3 et une raison d'une ligne. L'utilisateur corrige.
3. « Veux-tu un ou deux sièges sans carnet, au bon sens pur (par exemple un gestionnaire prudent) ? » Deux au plus, marqués « non sourcé ».

Range tout dans `wiki/maps/sieges-roast.json` :
```json
{"sieges": {"offre": {"nom": "Expert offre", "pilier": "offre, prix", "carnet": "expert-offre", "angle": "une ligne"}},
 "types": {"business": {"rapide": ["offre", "fond", "methode", "prudent"], "complet": [{"id": "offre", "poids": 3}]}}}
```

## Construire
1. **Poser les outils** (Claude) : copier `outils/roast.py` et `outils/siege-systeme.md` dans `scripts/roast/` du vault. `python scripts/roast/roast.py selftest` doit imprimer `selftest OK`.
2. **Écrire le skill de séance** (Claude) dans `.claude/skills/roast/SKILL.md` du vault, avec ce protocole :
   - **Annonce** (une ligne) : mode, sièges, tours, nombre de questions aux carnets, durée estimée.
   - **Brief** (250 mots au plus) dans `outputs/roast/<date>-<sujet>/session.json` : la décision, les options A, B, C (toujours une option « ne rien changer » ou « répartir » quand elle existe), le contexte chiffré avec les hypothèses marquées « (supposé) », ce qui compte comme réussite, le penchant de l'utilisateur s'il l'a dit (le comité le teste, il ne le répète pas). Plus la liste des sièges avec leur poids.
   - **Ancrage** : pour chaque siège ancré, un fichier `ancrage-<siege>.txt` avec UNE question dense (gabarit OPTIONS de `routage-carnets`), puis `python scripts/nlm_ask.py ask <carnet> ancrage-<siege>.txt --sortie <dossier>`. Une réponse refusée par le garde-fou se relance une fois ; refusée encore, le siège passe « non sourcé » pour la séance.
   - **Tour 1, avis d'ouverture** : un fichier `prompts/r1-<siege>.txt` par siège, avec son identité, son ancrage collé MOT POUR MOT, le brief, et le format de carte ci-dessous. Puis `python scripts/roast/roast.py tour <dossier> 1`.
   - **Désaccords** : la session écrit 1 à 3 points de désaccord de fond. Si tous choisissent la même option à un point près, la meilleure option non défendue devient un point de désaccord et un siège est chargé de la défendre à fond.
   - **Tour 2, réponses croisées** : cartes du tour 1 mélangées et nommées « Avis 1 » à « Avis n » (correspondance gardée), résumées en 3 lignes chacune ; chaque siège sait lequel est le sien, reçoit à nouveau son ancrage mot pour mot, et doit contester un avis, concéder le meilleur point adverse, et ne bouger que pour un meilleur argument. `roast.py tour <dossier> 2`.
   - **Tour 3, vote** (mode complet, ou si l'écart sur l'option en tête dépasse 3 points) : un projet de résolution, chaque siège vote Pour, Pour avec amendement, ou Contre.
   - **Verdict** : `python scripts/roast/roast.py scores <dossier>`, puis la session pèse les arguments (elle peut contredire la majorité en le disant), cherche à casser sa propre recommandation, et écrit : trois lignes de résumé, la décision, le seul bémol, trois prochaines étapes datées, l'angle mort de tous, l'avis minoritaire le plus fort.
3. **Format de carte du tour 1** (à mettre dans le skill) :
   ```
   {"position": "Oui franc | Oui | Oui sous conditions | Non | Non franc", "option": "A",
    "notes": {"A": 0, "B": 0, "C": 0}, "confiance": 1, "ruine": "aucun | possible | probable",
    "porte": "aller simple | aller-retour", "pourquoi": ["3 arguments, chacun nomme son principe"],
    "citations": ["0 à 2 phrases copiées mot pour mot de ton ancrage"], "risque": "...",
    "changer_avis": "le fait qui te ferait changer d'avis", "cette_semaine": "une action"}
   ```
4. **Contrôle des citations** : avant de montrer le verdict, la session vérifie que chaque citation d'une carte figure mot pour mot dans l'ancrage du siège. Une citation absente se retire.

## Test
Une séance réelle en mode rapide va au bout : au moins 3 sièges ancrés acceptés par le garde-fou, des cartes pour chaque siège au tour 1 et au tour 2, `scores.json` écrit, et chaque citation retrouvée mot pour mot dans son ancrage.

## Pièges vécus
- **Une question au carnet par tour, c'est trop.** Le quota et le temps fondent. Une question par siège avant le débat, et au plus deux appels ciblés en plus si le débat bute sur un fait que l'ancrage ne couvre pas.
- **Les sièges ne touchent à rien.** Sans accès aux fichiers, ils ne peuvent ni lire des données privées, ni lancer des questions aux carnets en douce. Le lanceur `claude -p` sans outils, dans un dossier neutre, le garantit.
- **Citation reprise d'un résumé.** Quand l'ancrage était résumé dans le prompt, des sièges ont « cité » le résumé. D'où l'ancrage collé mot pour mot à chaque tour où le siège peut citer.
- **La déférence envers un nom.** Les cartes du tour 2 sont anonymes : un siège ne suit pas un avis parce qu'il vient de l'expert le plus connu.
- **Simulation, jamais la personne.** Les sièges parlent depuis un carnet de sources ; le verdict le dit. Un auteur gardé interne n'apparaît jamais nommé dans une reprise publique du verdict.
- **Les options de la commande `claude` évoluent.** Si `roast.py tour` échoue partout, lancer `claude --help` et ajuster la ligne `cmd` de `siege()`. En repli, un sous-agent sans outils, plus cher.

## Entretien dans le temps
- Après chaque séance : la décision prise et, plus tard, son résultat vont dans la mémoire. Une fois par trimestre, comparer verdicts et résultats, et ajuster les poids des sièges.
- Le coût réel de chaque séance est dans `couts.json` : s'en servir pour l'annonce suivante.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, `wiki/maps/sieges-roast.json` si un siège a changé. Propose ensuite `board-textes`.
