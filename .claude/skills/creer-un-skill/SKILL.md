---
name: creer-un-skill
description: "Apprend à transformer un travail qui revient en skill ou en commande Claude Code : choisir entre les deux, écrire une description qui déclenche, structurer les étapes, joindre un script, tester. Utiliser quand l'utilisateur dit « je fais toujours la même chose », « crée une commande pour ça », « fais-en un skill », « automatise cette recette ». Pas pour améliorer un skill qui existe (utiliser ameliorer-les-skills)."
---
# Créer un skill ou une commande

## Pourquoi
Le système d'origine compte des centaines de skills et de commandes. Ceux qui servent ont tous la même forme : une description qui dit QUAND les lancer avec les mots réels de la personne, des étapes courtes, un test. Les autres ne se déclenchaient jamais : un audit a trouvé une grande majorité de commandes sans description, que Claude ne pouvait donc pas choisir seul. Ce skill transmet la forme qui marche.

## Prérequis
- coeur-claude-md, format-et-autonomie.
- Python 3 pour l'outil de vérification (`python --version`).
- Aucun coût.

## Interview
Lis d'abord : `.claude/skills/` et `.claude/commands/` (ne recrée jamais un skill qui existe), `wiki/maps/routage.md`, `log.md` (le travail a peut-être déjà été fait à la main, avec ses étapes).

Puis demande :
1. « Quel travail tu refais souvent ? Raconte-moi la dernière fois, étape par étape. » (devient la section Construire).
2. « Avec quels mots tu me le demandes d'habitude ? » (deviennent le déclencheur de la description, mot pour mot).
3. « Comment tu sais que c'est bien fait ? » (devient le Test).
4. « Qu'est-ce qui a déjà raté ? » (devient les Pièges).
5. « Avec quoi on pourrait le confondre ? » (devient le « Pas pour … »).

Range : le skill dans `.claude/skills/<nom>/SKILL.md` ou la commande dans `.claude/commands/<nom>.md`, la ligne de routage dans `wiki/maps/routage.md`.

## Construire

1. **Skill ou commande (3 min).** Claude choisit avec cette règle :
   | Si | Alors |
   |:-|:-|
   | une recette courte, un seul fichier, lancée surtout par `/nom` | commande `.claude/commands/<nom>.md` |
   | une recette avec scripts, gabarits ou références jointes, ou que Claude doit pouvoir choisir seul | skill `.claude/skills/<nom>/SKILL.md` + dossier `outils/` |
   Les deux se lancent par `/nom` et les deux ont une description qui déclenche.

2. **La description d'abord (5 min).** C'est la ligne la plus importante : Claude la lit pour décider s'il lance le skill. Format :
   `"<Ce que ça fait>. Utiliser quand l'utilisateur dit « … », « … ». Pas pour … (utiliser …)."`
   Mets les phrases réelles de la personne, pas des mots techniques. Ajoute la commande voisine à ne pas confondre.

3. **Écrire le corps depuis le gabarit (15 min).** Claude copie `outils/gabarit-SKILL.md`. Pour une commande, il garde seulement le frontmatter `description`, un titre et les étapes. Règles d'écriture :
   - Étapes numérotées, à l'impératif, chacune faisable en 20 minutes.
   - Une étape dit ce que Claude fait, ce que la personne fait, le fichier produit.
   - « Phase 0 » en tête si le skill doit lire des règles avant d'agir (par exemple la map de voix).
   - Ce qui doit rester exact (un format de sortie, un chemin) s'écrit en bloc de code.
   - Pas de règle déjà dans le cœur : pointe vers elle.

4. **Joindre un script quand une étape est mécanique (15 min).** Tout ce qui se calcule (compter, trier, vérifier, convertir) va dans un script dans `outils/` (ou `scripts/` du vault), pas dans des consignes. Un script : sans dépendance cachée, avec gestion d'erreur, une sortie claire, et un `--test` qui vérifie sa propre logique. Le skill dit la commande exacte à lancer.

5. **Vérifier la forme (2 min).** Claude copie `outils/verifier-skill.py` dans `scripts/` du vault une fois, puis lance `python scripts/verifier-skill.py .claude/skills/<nom>/SKILL.md`. Il corrige jusqu'à « Tout est conforme. »

6. **Le router (2 min).** Claude ajoute la ligne dans `wiki/maps/routage.md` : les phrases de la personne, puis `/nom`.

7. **L'essai réel (10 min).** Nouvelle conversation (les skills se chargent au démarrage). La personne dit sa phrase habituelle, sans prononcer le nom. Claude doit lancer le skill seul.

8. **Un skill qui existe ailleurs (5 min, si besoin).** Avant d'écrire, Claude cherche si un skill public fait déjà le travail (les plugins officiels, la commande `/plugin`). S'il en adopte un, il le filtre par les règles de la personne (voix, langue) et le note dans `wiki/maps/routage.md`. Il lit tout le fichier avant de l'installer : un skill est du code qui s'exécute.

## Test
Les deux sont vrais :
- `python scripts/verifier-skill.py .claude/skills/<nom>/SKILL.md` sort 0.
- Dans une nouvelle conversation, la phrase habituelle de la personne (sans le nom du skill) le déclenche.

## Pièges vécus
- **La description résumé.** « Gère les posts » ne dit pas quand lancer. Une description est un déclencheur, avec les mots de la personne.
- **Le skill géant.** Un skill qui fait tout devient illisible et Claude saute des étapes. Un skill par travail ; une chaîne appelle les skills l'un après l'autre.
- **Les consignes au lieu d'un script.** Demander à Claude de « vérifier qu'il n'y a pas de tiret long » marche une fois sur deux. Un script qui sort 0 ou 1 marche à chaque fois.
- **Les doublons.** Deux skills proches se volent les déclenchements. Avant d'en créer un, cherche dans `.claude/skills/` et `.claude/commands/`.
- **Le skill copié sans filtre.** Un skill public en anglais, recopié tel quel, a sorti des tournures que la personne interdisait. Toujours le passer par les règles de voix.

## Entretien dans le temps
- Le compteur de skills (hooks-ecrire) dit ceux qui ne servent jamais : réécris leur description ou archive-les.
- Chaque skill s'améliore avec ses transcriptions : voir ameliorer-les-skills.

## Après
Coche la ligne `creer-un-skill` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, la ligne dans `wiki/maps/routage.md`, puis propose la brique suivante : ameliorer-les-skills.
