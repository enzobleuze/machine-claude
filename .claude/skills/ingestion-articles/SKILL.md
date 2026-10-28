---
name: ingestion-articles
description: "Installe la capture des articles des auteurs de référence de la personne (Obsidian Web Clipper ou copie), une base dédoublonnée qui écarte les extraits et murs payants, et l'ingestion en pages sources et principes. Utiliser quand l'utilisateur dit « j'ai clippé des articles », « range les articles de mon auteur », « construis ma bibliothèque d'auteurs ». Pas pour un livre ou un PDF déposé (utiliser ingestion-fichiers)."
---
# Ingestion des articles d'auteurs

## Pourquoi
Dans le système d'origine, une part de la méthode s'appuyait sur un auteur de référence qui publie beaucoup en ligne. Les articles lus restaient dans le navigateur. Le clip vers le vault, puis une base qui compte les vrais mots, a réglé deux problèmes : on savait ce qui était déjà capturé, et on cessait de travailler sur des extraits de quelques lignes pris pour l'article entier (un mur payant ou une page de pub passait pour un texte complet). Leçon en plus : quand un auteur publie aussi en vidéo, coller la transcription sous l'article donne beaucoup plus de matière.

## Prérequis
- architecture-vault, ingestion-fichiers, recherche-par-le-sens conseillé.
- Obsidian Web Clipper (extension gratuite pour Chrome, Firefox, Safari, Edge). Sinon, copier-coller dans un .md.
- Python 3.9+.

## Interview
Lis d'abord : `wiki/sources/` (auteurs déjà présents), `wiki/maps/architecture.md`.

Puis demande :
1. « Quels auteurs font autorité dans ton métier, pour toi ? » Ex. pour une boulangère : des livres et blogs de technique ; pour un coach : les auteurs qu'il cite. Note 1 à 5 noms.
2. « Où publient-ils ? » (blog, newsletter, vidéo). Note les adresses.
3. « Tu veux pouvoir les citer en public, ou c'est une inspiration interne ? » Règle de citation dans `wiki/maps/auteurs.md`.

Range tout dans `wiki/maps/auteurs.md` : un paragraphe par auteur (où il publie, règle de citation, lien vers sa page source), 3 liens.

## Construire
1. **Web Clipper (10 min, ses mains).** Installer l'extension depuis obsidian.md/clipper. Dans ses réglages : coffre = le vault, dossier = `raw/articles/{{author}}` ou un dossier par auteur créé à la main (`raw/articles/<auteur>/`). Vérifie que le modèle remplit `source` (l'adresse de la page) et `title` dans le frontmatter : c'est le réglage par défaut.
2. **Premier clip (3 min, ses mains).** Il ouvre un article, clique sur l'extension, « Ajouter à Obsidian ». Claude vérifie le fichier dans `raw/articles/`.
3. **Base (2 min).** Copie `outils/articles-db.py` vers `scripts/`, puis :
   ```bash
   python scripts/articles-db.py --seuil 400
   ```
   Il écrit `wiki/sources/articles-db.md` : date, auteur, titre, mots, statut `ok` ou `court`. Un article reclippé plus long remplace l'ancienne ligne. Ajuste le seuil à la longueur habituelle de l'auteur.
4. **Transcriptions vidéo (optionnel, 5 min).** Si l'article a sa vidéo, colle la transcription à la fin du fichier sous un titre `## Transcription`. Elle compte dans les mots et nourrit l'ingestion.
5. **Commande (5 min).** `.claude/commands/ingest-articles.md` :
   ```markdown
   ---
   description: "Ingère les articles d'auteurs clippés. Utiliser quand on dit « j'ai clippé des articles », « /ingest-articles »."
   ---
   1. `python scripts/articles-db.py`. Ne traite que les lignes `ok` pas encore ingérées.
   2. Pour chaque article : enrichis `wiki/sources/auteur-<nom>.md` (idées clés avec citation exacte et lien
      vers le fichier raw), et les principes concernés dans `wiki/principes/` (cherche d'abord avec /cerveau).
   3. Les lignes `court` : signale-les (extrait ou mur payant), propose de reclipper la version complète.
   4. index, log, `python scripts/raw-nouveaux.py --marquer <fichiers>`.
   ```
6. **Route (1 min).** Ligne « j'ai clippé des articles » dans `wiki/maps/routage.md`.

## Test
Après trois clips : `wiki/sources/articles-db.md` a trois lignes (ou moins s'il y a un doublon d'adresse), un extrait volontairement court est marqué `court`, et la page `auteur-<nom>.md` cite chaque article avec un lien qui marche.

## Pièges vécus
- Extrait de mur payant ingéré comme un article complet : le contenu inventait le reste. Le compte de mots nettoyés et le statut `court` l'empêchent.
- Le même article clippé deux fois : doublon dans les principes. La base dédoublonne par adresse.
- Phrases d'un auteur réécrites puis attribuées à la personne : la règle « qui a dit quoi » du bibliothécaire s'applique, et le nom de l'auteur ne sort en public que si la règle de citation le permet.
- Chiffres d'un article repris sans la source : tout chiffre cité garde son lien vers l'article.

## Entretien dans le temps
Le jardinier peut relancer `articles-db.py` chaque nuit. Une fois par mois, regarde les auteurs dont rien n'a été clippé depuis longtemps et demande s'ils comptent encore.

## Après
Coche la ligne `ingestion-articles` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose la source suivante de son interview, ou le bloc B si toutes sont branchées.
