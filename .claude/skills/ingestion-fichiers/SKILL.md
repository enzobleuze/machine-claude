---
name: ingestion-fichiers
description: "Installe le geste « ingère » : la personne dépose n'importe quel fichier dans raw/, Claude le lit, présente un plan, crée ou enrichit les pages du wiki, relie, met à jour index et journal, et branche les règles nouvelles là où elles agissent vraiment. Utiliser quand l'utilisateur dit « ingère », « j'ai déposé dans raw », « range ce document », « installe /ingest ». Pas pour Google Drive, Notion, les appels, les réseaux ou les articles d'auteurs (skills ingestion-drive, ingestion-notion, ingestion-appels, ingestion-reseaux, ingestion-articles)."
---
# Ingestion des fichiers déposés

## Pourquoi
Dans le système d'origine, la personne ne fait qu'une chose : déposer dans raw/ et dire « ingère ». Tout le reste est le travail de Claude. Deux leçons ont façonné ce geste. Première leçon : un document résumé dans une fiche source puis oublié ne change rien, car le réflexe manquant était de brancher la règle nouvelle dans la mémoire, les skills et les tâches de nuit. Deuxième leçon : les erreurs du wiki (liens morts, doublons) sont celles de Claude, il les répare sans demander à la personne de trancher.

## Prérequis
- architecture-vault, memoire-fichiers, bibliothecaire-installer faits.
- Python 3.9+. Aucun coût.

## Interview
Lis d'abord : `wiki/maps/architecture.md` (tiroirs, zones privées), `index.md`, `wiki/maps/etageres.md`.

Puis demande :
1. « Quels types de documents vas-tu déposer le plus ? » (notes, PDF de formation, livres, comptes rendus, exports, captures). Pour chaque type, décide avec lui le tiroir d'arrivée et note-le dans le tableau de l'étape 2.
2. « Veux-tu valider mon plan avant chaque ingestion, ou seulement quand il y a beaucoup de fichiers ? » Par défaut : plan détaillé sous 10 fichiers, compteurs et échantillon au-delà, puis validation.
3. « Y a-t-il des documents avec des données personnelles de tiers ? » Si oui, règle d'anonymisation pour tout ce qui sort en public.

## Construire
1. **Outil de repérage (2 min).** Copie `outils/raw-nouveaux.py` vers `scripts/`. `python scripts/raw-nouveaux.py` liste ce qui attend. Après une ingestion réussie : `python scripts/raw-nouveaux.py --marquer raw/a.pdf raw/b.md`.
2. **Table de routage par type (5 min).** Écris `wiki/maps/ingestion.md` (frontmatter standard, 3 liens) avec ce tableau, adapté à l'interview :
   | Type | Ce que Claude crée ou enrichit |
   |:-|:-|
   | Livre, formation | `wiki/sources/source-<auteur>-<titre>.md` + principes clés dans `wiki/principes/` |
   | Notes, journal | la page du thème existant, sinon une nouvelle page |
   | Compte rendu d'un client | sa fiche dans `wiki/clients/` (section historique datée) |
   | Contenu publié | fiche dans `wiki/contenu/` (date, angle, ce qui a marché) |
   | Ses réponses vécues (interviews, mémos vocaux transcrits) | les scènes et phrases exactes dans la carte du vécu, jamais résumées |
   | CSV ou export d'outil | un script dédié dans `scripts/`, pas un copier-coller |
3. **La commande (5 min).** Écris `.claude/commands/ingest.md` :
   ```markdown
   ---
   description: "Ingère les nouveaux fichiers de raw/ dans le wiki. Utiliser quand on dit « ingère », « j'ai déposé dans raw », « /ingest »."
   ---
   # /ingest
   1. Repère : `python scripts/raw-nouveaux.py`. Argument = un seul fichier ou `depuis AAAA-MM-JJ`.
   2. Lis chaque fichier en entier (PDF compris). Identifie son type avec wiki/maps/ingestion.md.
   3. Plan : sous 10 fichiers, liste fichier par fichier (pages créées, pages enrichies) ;
      au-delà, compteurs + 3 exemples. Attends le oui.
   4. Exécute : enrichis avant de créer (cherche d'abord avec /cerveau si la page existe),
      frontmatter standard, au moins 3 [[liens]] vérifiés, liens retour sur les pages touchées.
      Garde les mots exacts des personnes entre guillemets. N'écris jamais dans raw/.
   5. Branchement (les 6 questions) : cette info change-t-elle un skill ? doit-elle aller en
      mémoire ? justifie-t-elle un hook ? remplace-t-elle une règle (marque l'ancienne
      périmée) ? doit-elle entrer dans le prompt d'une tâche de nuit ? demande-t-elle un chantier ?
      Applique ce qui est sûr, propose le reste.
   6. index.md, entrée log.md, puis `python scripts/raw-nouveaux.py --marquer <fichiers>`.
   7. Rapport : pages créées, pages enrichies, branchements faits, doublons et trous repérés.
   ```
4. **Route (1 min).** Ligne « ingère » dans `wiki/maps/routage.md` vers `/ingest`.
5. **Essai à vide (5 min).** Dépose un vrai document de la personne dans raw/, lance `/ingest`, montre-lui le plan, exécute après son oui.

## Test
Après l'essai : `python scripts/raw-nouveaux.py` affiche « 0 fichier(s) à ingérer », la nouvelle page a ses 3 liens (le hook ne proteste pas), `log.md` a l'entrée du jour, et `python scripts/lint_wiki.py` ne montre aucun lien mort neuf.

## Pièges vécus
- Ingestion qui s'arrêtait à la fiche résumé : la règle nouvelle ne s'appliquait jamais. Les 6 questions de branchement sont devenues obligatoires.
- Doublons : une nouvelle page créée alors qu'une page proche existait sous un autre nom. Toujours chercher par le sens avant de créer.
- Volume énorme d'un coup : plan illisible. Au-delà de 10 fichiers, compteurs et échantillon.
- Demander à la personne « je crée la page ou je retire le lien ? » : déplacé, c'est une décision technique que Claude prend seul.
- Le vécu de la personne résumé en langage lisse : on perd ce qui fait sa valeur. Ses phrases sont gardées mot pour mot.

## Entretien dans le temps
La tâche de nuit peut lancer `raw-nouveaux.py` et signaler dans le résumé du matin les fichiers en attente depuis plus de 3 jours. Toute nouvelle sorte de document ajoute une ligne à `wiki/maps/ingestion.md`.

## Après
Coche la ligne `ingestion-fichiers` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose lint-wiki. Les ingestions de ses autres sources (Drive, Notion, appels, réseaux, articles) viennent après sauvegardes-3-lieux, dans l'ordre de ce qu'il utilise le plus.
