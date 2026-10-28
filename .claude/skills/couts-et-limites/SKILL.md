---
name: couts-et-limites
description: "Explique et règle ce qui consomme le forfait Claude (sessions, sous-agents, appels claude -p de nuit, images, connecteurs) et pose les économies qui ne coûtent rien en qualité : cœur court, planche contact pour les images, texte avant capture, appels de nuit allégés. Utiliser quand l'utilisateur dit « j'ai atteint ma limite », « ça consomme trop », « combien ça coûte », « mes tâches de nuit se sont arrêtées ». Pas pour choisir un modèle (utiliser sous-agents-modeles)."
---
# Coûts et limites

## Pourquoi
Le système d'origine fait tourner des sessions longues le jour et des dizaines de tâches automatiques la nuit, sur un seul abonnement. Deux fois, la limite de la semaine a été atteinte et les tâches de nuit se sont arrêtées net. En cherchant, on a trouvé où partaient les jetons : un gros cœur relu à chaque appel, des connecteurs chargés pour rien, des images lues une par une. Les corrections n'ont rien enlevé à la qualité. Leçon de l'autre côté : la personne préférait des conversations longues et autonomes à des économies qui font travailler Claude moins bien.

## Prérequis
- coeur-claude-md, sous-agents-modeles.
- Le socle : `scripts/planche.py` (copié depuis `outils/planche.py`). Il demande Python avec Pillow (`pip install pillow`) et, pour les vidéos, ffmpeg.

## Interview
Lis d'abord : `wiki/maps/modeles.md`, `~/.claude/settings.json` (modèle, effort), la liste des connecteurs (`claude mcp list`), les tâches planifiées s'il y en a (bloc F), `log.md` (incidents de limite).

Puis demande :
1. « Quel abonnement as-tu, et as-tu déjà atteint ta limite ? Quand ? »
2. « Tu préfères que je travaille longtemps et à fond, ou que j'économise au maximum ? » (la réponse la plus fréquente : à fond, tant qu'il reste de la marge).
3. « As-tu une clé API Anthropic payée à l'usage, en plus de l'abonnement ? » (si oui, elle se facture à part : jamais par accident).
4. « Tu travailles souvent avec des images ou des vidéos ? » (décide l'importance de la planche contact).

Range : les réponses dans le fichier mémoire `feedback_couts.md` et dans `wiki/maps/couts.md`.

## Construire

1. **Ce qui consomme, en clair (10 min).** Claude écrit `wiki/maps/couts.md` avec ces repères, vérifiés sur la page officielle du support Anthropic du jour (les règles ont changé plusieurs fois en un an) :
   - L'abonnement a une limite sur quelques heures et une limite par semaine. `/usage` (ou `/cost` selon la version) montre où tu en es.
   - Les sessions, les sous-agents et les appels `claude -p` lancés par des tâches planifiées puisent dans la même limite. Une tâche de nuit gourmande mange la marge du lendemain.
   - Une clé API (`ANTHROPIC_API_KEY`) se facture à part, au tarif public. Si elle est dans l'environnement, Claude Code peut l'utiliser à la place de l'abonnement : vérifie qu'elle n'y est pas par erreur.
   - Chaque message relit toute la conversation (avec un cache qui rend la relecture moins chère). Plus la conversation est longue, plus chaque message pèse.
   - Chaque appel automatique relit le cœur, la mémoire, la liste des outils et des connecteurs : un coût fixe de plusieurs dizaines de milliers de jetons par appel, avant le moindre travail.

2. **La planche contact pour les images (5 min).** Une image lue coûte environ 1 500 jetons et reste dans la conversation à chaque tour. Claude ajoute au cœur : « Avant de regarder une série d'images ou une vidéo : `python scripts/planche.py <dossier|motif|vidéo> -o planche.jpg` (16 cases maximum, le prix d'une seule image), puis ouvre en grand seulement l'image choisie. » Il teste sur un dossier d'images de la personne.

3. **Le texte avant la capture (2 min).** Dans le cœur : « Dans un navigateur, lis le texte de la page avant de prendre une capture. La capture sert à juger un visuel. »

4. **Le cœur court (rappel, 2 min).** Le premier levier du coût fixe est la taille du `CLAUDE.md` et de l'index mémoire (coeur-claude-md). Claude vérifie qu'ils respectent leur plafond.

5. **Les connecteurs inutiles (10 min).** Chaque connecteur MCP actif ajoute la liste de ses outils au contexte. Claude liste les connecteurs (`/mcp`), demande lesquels servent vraiment chaque semaine, et désactive les autres (ils se rebranchent en une commande). Pour les appels de nuit qui n'en utilisent aucun, voir claude-sans-fenetre (option `--strict-mcp-config`).

6. **Mesurer avant de décider (15 min, quand un doute coûte).** Pour un appel automatique, `claude -p "<consigne>" --output-format json` rend un champ `total_cost_usd` et le détail des jetons (écrits en cache, relus). Sur abonnement, ce montant est un équivalent au tarif public, utile pour comparer deux réglages, pas une facture. Claude note la mesure avant et après chaque changement dans `wiki/maps/couts.md`.

7. **Les modèles locaux pour le mécanique (option, voir outils-locaux).** Trier, extraire un champ, classer oui ou non peut partir sur un modèle gratuit installé sur l'ordinateur. Jamais un texte dans la voix de la personne.

8. **Le garde-fou de limite (5 min).** Dans le cœur : « Si une tâche ou un appel tombe sur une erreur de limite, ne relance pas en boucle : note-le, reporte au lendemain, préviens la personne seulement si c'est urgent. » Les scripts de nuit (bloc F) s'arrêtent proprement sur ce message et reprennent la nuit suivante.

## Test
Les deux sont vrais :
- `python scripts/planche.py <un dossier d'images> -o planche.jpg` produit une planche, et la ligne affichée annonce un coût en jetons plus petit que la somme des images.
- `wiki/maps/couts.md` existe, cite la date de vérification de la page officielle, et liste les connecteurs gardés avec leur raison.

## Pièges vécus
- **Un crédit annoncé, puis suspendu.** Un changement de facturation des appels automatiques a été annoncé, préparé avec des garde-fous, puis suspendu par l'éditeur. Des alertes ont continué à compter un crédit qui n'existait pas. Relis la page officielle avant de bâtir une règle de coût, et date ta vérification.
- **Le coût fixe de chaque appel.** Des tâches de quelques lignes coûtaient cher parce que chaque appel relisait le cœur, la mémoire et la liste de tous les connecteurs. Cœur court et appels allégés l'ont divisé plusieurs fois.
- **Une heure dans le contexte.** Une heure injectée au démarrage changeait le début du prompt à chaque minute et empêchait le cache de servir. Rien de changeant au début du contexte.
- **Économiser contre la personne.** Un compactage automatique prêt à brancher a été refusé : la personne avait peur que Claude oublie. Les économies gratuites d'abord (planche, texte avant capture, appels de nuit allégés), le reste seulement si la limite bloque.
- **Les images une par une.** Juger douze vignettes une à une coûtait douze fois plus que la planche, pour la même décision.

## Entretien dans le temps
- Chaque lundi (plan de la semaine, bloc F), Claude regarde la jauge `/usage` et la note dans `wiki/maps/couts.md`.
- À chaque nouvelle tâche planifiée : sa mesure en jetons dans `wiki/maps/couts.md`.

## Après
Coche la ligne `couts-et-limites` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, puis propose la brique suivante : claude-sans-fenetre.
