---
name: ingestion-drive
description: "Installe un dossier « Dépôt » dans Google Drive que Claude vide tout seul : il lit chaque fichier, le renomme proprement, le range dans le bon tiroir, met de côté ce dont il doute, ne supprime jamais rien. Utiliser quand l'utilisateur dit « range mon Drive », « vide le Dépôt », « j'ai déposé des fichiers dans le Drive », « /ingest-drive ». Pas pour les fichiers déposés dans raw/ (utiliser ingestion-fichiers)."
---
# Ingestion Google Drive (le Dépôt)

## Pourquoi
Dans le système d'origine, le Drive était un grenier : factures, photos, captures, documents de travail mélangés, noms comme « IMG_4821 ». La personne dépose maintenant tout dans un seul dossier `_Depot`, et Claude le vide : il lit le contenu, choisit le tiroir, renomme en `AAAA-MM-JJ_description.ext`. Ce qui le fait douter va dans `_a-clarifier` avec une question. Le Dépôt finit toujours vide et rien n'est jamais supprimé.

## Prérequis
- architecture-vault, securite-git-secrets (le hook anti-suppression doit être branché).
- Google Drive pour ordinateur installé (Windows ou Mac) et connecté. Gratuit.
- Python 3.9+.
- Optionnel : la tâche de nuit (bloc F) pour le tri automatique.

## Interview
Lis d'abord : `wiki/maps/architecture.md` (zones privées), une éventuelle carte `wiki/maps/google-drive.md`.

Puis demande :
1. « Ouvre ton Drive dans l'explorateur de fichiers : quels grands dossiers tu as déjà ? » Fais la liste avec lui. Propose une structure de 5 ou 6 tiroirs maximum, par ex. Activité (Contenu, Offres, Clients), Images, Administratif (Factures, Impôts, par année), Personnel, Archive.
2. « Y a-t-il des dossiers de travail que je ne dois jamais déplacer ? » (dossiers partagés, dossiers d'entrée d'autres outils). Ils iront dans `--garder`.
3. « À partir de quelle certitude je range seul ? » Défaut : 85 sur 100. En dessous, `_a-clarifier`.
4. « Tu veux que je trie la nuit, ou seulement quand tu le demandes ? »

Range la structure dans `wiki/maps/google-drive.md` (arbre des tiroirs, règle de nommage, dossiers gardés, seuil), avec 3 liens.

## Construire
1. **Trouver le Drive (3 min).** Windows : souvent `G:\My Drive` ou `G:\Mon Drive` (lettre variable). Mac : `~/Library/CloudStorage/GoogleDrive-<adresse>/My Drive`. Crée dedans `_Depot` et `_Depot/_a-clarifier`. Guide-le si Drive pour ordinateur est en mode « streaming » : les fichiers restent lisibles, c'est bon.
2. **Outil (2 min).** Copie `outils/depot-scan.py` vers `scripts/`. Essai :
   ```bash
   python scripts/depot-scan.py scan --garder dossier-partage
   ```
   Il liste chaque fichier avec un nom propre proposé (ASCII, minuscules, tirets, date en tête).
3. **Créer les tiroirs (5 min).** Crée les dossiers de la structure validée (noms en ASCII avec tirets : `Administratif/Factures/2026`). Ne déplace encore rien d'ancien sans son accord.
4. **La commande (5 min).** Écris `.claude/commands/ingest-drive.md` :
   ```markdown
   ---
   description: "Vide le Dépôt Google Drive : lit, renomme, range, ne supprime jamais. Utiliser quand on dit « range mon Drive », « vide le Dépôt », « /ingest-drive »."
   ---
   # /ingest-drive
   1. `python scripts/depot-scan.py scan --garder <dossiers gardés>` (liste dans wiki/maps/google-drive.md).
   2. Lis le CONTENU de chaque fichier : texte et PDF avec Read, image par la vue. Décide tiroir,
      nom (date trouvée DANS le document, sinon date du fichier) et certitude sur 100.
   3. Certitude au seuil ou plus : `python scripts/depot-scan.py deplacer "<fichier>" "<tiroir>" --nom <nom> --confiance <n>`.
      En dessous : même commande vers `_Depot/_a-clarifier`, puis une ligne dans wiki/maps/drive-en-attente.md
      (fichier, meilleure hypothèse, 2 ou 3 options, date).
   4. Jamais de suppression. Un dossier vidé part dans Archive/Coquilles-vides.
   5. Rapport : N rangés, M à clarifier. Aucune donnée sensible (montant, numéro de compte) dans le rapport ni dans une notification.
   6. Quand la personne répond à une question en attente : déplace le fichier, marque la ligne RÉSOLU.
   ```
5. **Premier tri ensemble (10 min).** Dépose 5 fichiers variés, lance `/ingest-drive`, commente chaque choix avec lui. Ajuste la carte selon ses corrections (chaque correction devient une règle dans `wiki/maps/google-drive.md`).
6. **La nuit (optionnel, 5 min).** Avec le bloc F : une tâche planifiée lance `claude -p "/ingest-drive"` en mode automatique seulement si `depot-scan.py scan` trouve des fichiers. Windows : Planificateur de tâches. Mac : `launchd` ou `crontab -e`. Le résumé du matin dit seulement « N rangés, M à clarifier ».

## Test
Après le premier tri : `python scripts/depot-scan.py scan` renvoie une liste `fichiers` vide, chaque fichier déplacé a une ligne dans `outputs/ingest-drive/journal.csv`, et aucun fichier n'a disparu (compte avant et après égal, `_a-clarifier` compris).

## Pièges vécus
- Suppression tentée pour « nettoyer » : interdit. Le hook anti-suppression bloque, et le script ne sait que déplacer. Les vrais déchets vont dans Archive et la personne les supprime elle-même.
- Collision de noms qui écrasait un fichier : le script ajoute `-2`, `-3` et n'écrase jamais.
- Noms avec accents, esperluettes ou espaces : cassent les scripts et la lecture par une IA. Tout en ASCII avec tirets.
- Dossiers de travail d'autres outils triés par erreur : liste `--garder` obligatoire.
- Données sensibles dans une notification téléphone : le résumé ne contient que des compteurs.

## Entretien dans le temps
Chaque correction de la personne devient une règle de la carte. Une fois par mois, regarde `_a-clarifier` : un fichier qui y traîne depuis plus de 2 semaines mérite une question directe. Si un type revient souvent en doute, ajoute une règle claire pour lui.

## Après
Coche la ligne `ingestion-drive` dans `wiki/maps/parcours.md`, entrée dans `log.md`, ligne « range mon Drive » dans `wiki/maps/routage.md`, puis propose la source suivante de son interview, ou le bloc B si toutes sont branchées.
