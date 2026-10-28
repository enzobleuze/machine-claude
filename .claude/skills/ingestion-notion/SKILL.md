---
name: ingestion-notion
description: "Branche Notion au vault : une intégration en lecture, un script qui copie les bases partagées dans raw/notion-sync/ sans retélécharger ce qui n'a pas bougé, puis l'ingestion dans le wiki. Utiliser quand l'utilisateur dit « mes notes sont dans Notion », « synchronise Notion », « /pull-notion ». Pas pour les fichiers déposés à la main (utiliser ingestion-fichiers)."
---
# Ingestion Notion

## Pourquoi
Dans le système d'origine, une partie de l'historique vivait dans Notion : fiches clients, bibliothèque de prompts, archives d'emails, suivi de production. Claude ne pouvait rien en faire tant que c'était là-bas. Un script de copie incrémentale a réglé ça : Notion reste l'outil de saisie si la personne y tient, et le vault en garde une copie lisible que l'ingestion transforme en pages reliées. Le connecteur Notion de Claude reste utile pour une question ponctuelle, le script sert à la copie complète et répétée.

## Prérequis
- architecture-vault, ingestion-fichiers, securite-git-secrets (les secrets doivent vivre hors du vault).
- Un compte Notion. Gratuit pour cet usage.
- Python 3.9+.

## Interview
Lis d'abord : `wiki/maps/architecture.md`, `wiki/maps/ingestion.md`.

Puis demande :
1. « Quelles bases Notion comptent pour ton activité ? » (clients, idées, contenu, process). Note leurs noms exacts.
2. « Notion reste ton outil de saisie, ou on y migre une fois pour toutes ? » Si migration : un seul passage puis on arrête. Sinon : copie régulière.
3. « Dans ces bases, quelles données sont privées ? » (coordonnées, paiements). Elles restent dans raw/ et dans les fiches privées, jamais dans le contenu public.

Range les réponses dans `wiki/maps/notion.md` (bases suivies, mode, règles de confidentialité), avec 3 liens.

## Construire
1. **Créer l'intégration (5 min, ses mains).** Guide-le : ouvrir notion.so/profile/integrations (ou Réglages > Connexions > Développer ou gérer les intégrations), « Nouvelle intégration », nom « Lecture vault », type interne, capacités : lecture du contenu seulement. Copier le « Secret d'intégration interne ».
2. **Ranger le secret hors du vault (2 min).** Claude crée le fichier, la personne colle la valeur :
   Windows : `%USERPROFILE%\.claude\secrets\notion.env`. Mac : `~/.claude/secrets/notion.env`. Contenu : `NOTION_TOKEN=<le secret>`. Ne le colle jamais dans la conversation si elle peut l'éviter : ouvre le fichier dans un éditeur pour elle (`notepad` ou `open -e`).
3. **Partager les bases (5 min, ses mains).** Sur chaque base à suivre : menu « ... » en haut à droite > Connexions > ajouter « Lecture vault ». Sans ce geste, l'intégration ne voit rien.
4. **Script (2 min).** Copie `outils/pull-notion.py` vers `scripts/`. Vérifie la visibilité sans rien écrire :
   ```bash
   python scripts/pull-notion.py --essai
   ```
   Il liste les bases visibles. Une base manque : elle n'est pas partagée (étape 3).
5. **Première copie (5 min).** `python scripts/pull-notion.py`. Résultat : `raw/notion-sync/<base>/<page>-<id>.md`, un fichier par page, propriétés en liste, contenu en Markdown. L'état `_etat.json` évite de retélécharger.
6. **Ingestion (15 min).** Lance `/ingest` sur `raw/notion-sync/`. Règles : une fiche par personne dans `wiki/clients/`, les bibliothèques (prompts, emails) agrégées en une page source par base, jamais une page wiki par ligne de base sans intérêt.
7. **Régularité (optionnel, 5 min).** Avec le bloc F : tâche planifiée chaque nuit `python scripts/pull-notion.py`, puis l'ingestion le lendemain en session ou en tâche de nuit.

## Test
`python scripts/pull-notion.py` lancé deux fois de suite : la seconde fois affiche « 0 page(s) écrites » et autant d'« inchangées » que de pages. Et une page modifiée dans Notion réapparaît à jour au passage suivant.

## Pièges vécus
- Jeton rangé dans le vault puis poussé sur GitHub : l'historique git garde tout pour toujours. Les secrets vivent dans `~/.claude/secrets/`, et `sauvegarde-git.py` refuse de pousser un `.env`.
- Exporter en CSV à la main plutôt que copier par l'API : les CSV vieillissent le jour même. L'API est la source de vérité.
- Une page wiki par ligne de base : un wiki gonflé de pages vides. On agrège.
- Limite de débit de Notion (environ 3 requêtes par seconde) : le script fait une pause et réessaie seul sur les erreurs 429.

## Entretien dans le temps
Si le script sort le code 1, le jeton a été révoqué : recrée-le (étapes 1 et 2). Quand une nouvelle base devient importante, partage-la avec l'intégration et ajoute-la à `wiki/maps/notion.md`. En cas de migration finie, retire la tâche planifiée et note-le dans le journal.

## Après
Coche la ligne `ingestion-notion` dans `wiki/maps/parcours.md`, entrée dans `log.md`, ligne « synchronise Notion » dans `wiki/maps/routage.md`, puis propose la source suivante de son interview, ou le bloc B si toutes sont branchées.
