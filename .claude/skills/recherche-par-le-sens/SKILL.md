---
name: recherche-par-le-sens
description: "Installe la recherche par le sens dans le vault (embeddings locaux, gratuits, rien n'est envoyé sur internet) et son test d'or. Utiliser quand l'utilisateur dit « la recherche ne trouve pas », « cherche par le sens », « installe /cerveau », « vérifie le cerveau ». Pas pour la façon de répondre avec les notes (utiliser bibliothecaire-installer)."
---
# Recherche par le sens

## Pourquoi
Dans le système d'origine, la même idée vivait sous des formulations très différentes. La recherche par mot-clé ratait la scène sur « lâcher prise » parce que la note parlait d'un « orchestre qu'on arrête de diriger ». Un petit moteur local par le sens (des embeddings calculés sur la machine) a réglé ça, avec un gain mesuré sur le vault réel. Il est volontairement simple : un seul modèle, un cache disque, pas de base vectorielle. Et il retombe tout seul sur les mots-clés s'il manque une pièce, pour ne jamais casser une tâche.

## Prérequis
- architecture-vault et bibliothecaire-installer faits.
- Python 3.9+. Environ 200 Mo de disque pour le modèle, téléchargé une seule fois.
- Fichier du socle : `outils/cerveau.py` du repo. Ne le réécris pas.
- Aucun coût, aucune clé.

## Interview
Lis d'abord : `wiki/maps/etageres.md`, `wiki/maps/architecture.md` (zones privées), la liste des dossiers de `wiki/`.

Puis demande :
1. « Donne-moi trois choses que tu sais avoir écrites quelque part, avec tes mots de tous les jours. » Ex. « le jour où un client a failli abandonner ». Pour chacune, trouve la note avec lui : ce seront les tests d'or.
2. « Des dossiers à ne jamais indexer ? » Par défaut `wiki/finances/` et les archives sont exclus.

Range les tests dans `scripts/cerveau-tests.txt`, les exclusions dans la constante `EXCLUS` de `scripts/cerveau.py`.

## Construire
1. **Copier (2 min).** `outils/cerveau.py` du repo vers `scripts/cerveau.py` du vault. Le script calcule la racine du vault comme le parent de `scripts/` : garde cet emplacement.
2. **Installer le moteur (5 min).**
   ```bash
   python -m pip install fastembed numpy
   ```
   Mac : `python3 -m pip install --user fastembed numpy`. Windows, si plusieurs Python cohabitent : `py -3.12 -m pip install fastembed numpy`, et utilise ce même Python dans les tâches planifiées.
3. **Premier calcul (5 min).** `python scripts/cerveau.py "test"` : la première fois, il télécharge le modèle multilingue et calcule le sens de chaque paragraphe (cache dans `outputs/cerveau-cache.npz`, ignoré par git). Ensuite seuls les paragraphes modifiés sont recalculés.
4. **Exclusions (2 min).** Ajoute dans `EXCLUS` les dossiers privés de l'interview (ex. `("finances", "archive", "sante")`).
5. **Test d'or (5 min).** Copie `outils/cerveau-check.py` de ce skill vers `scripts/`. Écris `scripts/cerveau-tests.txt` :
   ```text
   # question avec d'autres mots que la note => chemin attendu
   le jour où un client a failli tout lâcher => wiki/clients/client-a.md
   comment je fixe mes prix => wiki/strategie/prix.md
   ```
   Puis `python scripts/cerveau-check.py`.
6. **Commande (1 min).** `.claude/commands/cerveau.md` (socle) lance déjà `python scripts/cerveau.py "$ARGUMENTS"` puis deux reformulations. Vérifie qu'elle est copiée.

## Test
`python scripts/cerveau-check.py` affiche « 3/3 tests passés » et chaque ligne montre le mode sens. Échec possible : ligne « mode mots-clés » = fastembed pas installé dans ce Python.

## Pièges vécus
- Index rangé dans un dossier synchronisé par une app de cloud : fichiers verrouillés et conflits. Garde le cache dans `outputs/` exclu de la synchro, ou déplace `CACHE` vers un dossier local (`%LOCALAPPDATA%` sous Windows, `~/Library/Caches` sur Mac).
- Moteur installé dans un Python et tâche de nuit lancée avec un autre : la recherche tombait en mots-clés sans prévenir. Le test d'or attrape ce cas, lance-le après toute mise à jour de Python.
- Notes privées remontées dans une réponse : les exclusions se règlent AVANT le premier calcul.
- Modèle anglais sur un vault en français : résultats médiocres. Le modèle multilingue du script est le bon choix par défaut.

## Entretien dans le temps
Le jardinier relance le test d'or chaque nuit (étape facultative dans la brique jardinier) et signale un échec dans son résumé. Chaque fois qu'une recherche rate une note qui existait, ajoute une ligne au test d'or.

## Après
Coche la ligne `recherche-par-le-sens` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose ingestion-fichiers.
