---
name: lint-wiki
description: "Installe le bilan de santé du wiki (liens morts, orphelines, pages maigres, frontmatter, moins de 3 liens, index désynchronisé) et la règle : Claude répare lui-même l'hygiène technique. Utiliser quand l'utilisateur dit « audit du wiki », « lint », « vérifie la santé du wiki », « /lint ». Pas pour vérifier le moteur de recherche (utiliser recherche-par-le-sens) ni pour l'entretien de nuit (utiliser jardinier)."
---
# Bilan de santé du wiki (lint)

## Pourquoi
Dans le système d'origine, une notification a annoncé un jour plus d'un millier de liens morts. Claude a demandé au fondateur s'il fallait créer les pages ou retirer les liens. Réponse : « le wiki, c'est toi qui l'écris ; si il y a des erreurs, c'est toi qui sais comment réparer ». Depuis, le bilan sépare deux choses : l'hygiène technique (liens, frontmatter, index), que Claude répare seul avec une règle sûre, et les vraies questions de fond (deux pages qui se contredisent), seules soumises à la personne.

## Prérequis
- architecture-vault fait. Python 3.9+. Aucun coût.

## Interview
Lis d'abord : `wiki/maps/architecture.md` (zones privées), le dernier bilan dans `outputs/lint/` s'il existe.

Puis demande une seule chose : « Tu veux voir le bilan à chaque fois, ou seulement quand il y a une contradiction de fond à trancher ? » Défaut : seulement les contradictions. Range la réponse dans `wiki/maps/lint.md`.

## Construire
1. **Outil (2 min).** Copie `outils/lint_wiki.py` vers `scripts/lint_wiki.py` (le nom avec tiret bas compte : le jardinier l'importe). Vérifie : `python scripts/lint_wiki.py --test` puis `python scripts/lint_wiki.py`.
2. **Règles de réparation (5 min).** Écris dans `wiki/maps/lint.md` les règles que Claude applique sans demander :
   - lien mort vers une page qui existe sous un nom proche : corriger le lien ;
   - lien mort vers un concept qui revient dans plusieurs pages : créer la page (frontmatter, 3 liens, contenu tiré des pages qui en parlent) ;
   - lien mort isolé sans valeur : retirer les crochets, garder le texte ;
   - orpheline : l'ajouter à la carte ou au `_index.md` de son dossier ;
   - moins de 3 liens : ajouter des liens vers des pages vraiment proches (cherche avec /cerveau) ;
   - frontmatter incomplet : le jardinier complète la nuit, sinon compléter ;
   - page maigre : enrichir depuis raw/ ou fusionner avec la page voisine (archiver l'ancienne, jamais supprimer).
   Plafond de sécurité : au-delà de 100 réparations d'un coup, faire un commit avant et un après.
3. **La commande (5 min).** `.claude/commands/lint.md` :
   ```markdown
   ---
   description: "Bilan de santé du wiki et réparations sûres. Utiliser quand on dit « audit du wiki », « lint », « /lint »."
   ---
   1. `python scripts/lint_wiki.py --json > outputs/lint/AAAA-MM-JJ.json` (crée le dossier).
   2. Applique les règles de wiki/maps/lint.md, sans demander. Commit avant si plus de 100 changements.
   3. Contradictions : relis les principes qui parlent du même sujet ; si deux pages se contredisent,
      montre les deux phrases et demande laquelle garder. C'est la seule question posée.
   4. Relance `python scripts/lint_wiki.py` et donne : avant, après, ce qui reste.
   5. Entrée dans log.md.
   ```
4. **Route (1 min).** Ligne « audit du wiki » dans `wiki/maps/routage.md`.
5. **Premier passage (10 à 20 min).** Lance `/lint`, montre le avant et après.

## Test
Après `/lint` : `python scripts/lint_wiki.py --strict` sort le code 0 (aucun lien mort), et le nombre d'orphelines a baissé. Le hook des 3 liens reste silencieux sur les pages réparées.

## Pièges vécus
- Demander à la personne de trancher une erreur technique de Claude : perte de temps et de confiance. Elle ne voit que les contradictions de fond.
- Liens morts en boule de neige : une page renommée casse des dizaines de liens. Obsidian met à jour les liens s'il fait le renommage ; quand Claude renomme, il corrige les liens dans la même opération.
- Réparation de masse sans commit : impossible à défaire proprement. Commit avant, commit après.
- Liens écrits à l'intérieur de blocs de code comptés comme des liens : l'outil ignore le code.

## Entretien dans le temps
Le jardinier compte les liens morts et orphelines chaque nuit et les met dans son résumé. Un `/lint` complet une fois par semaine (ou quand le résumé montre une hausse). Une notification seulement si le nombre augmente d'une semaine à l'autre.

## Après
Coche la ligne `lint-wiki` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose jardinier.
