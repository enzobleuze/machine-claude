---
name: architecture-vault
description: "Pose l'architecture du second cerveau : raw/ immuable, wiki/ tenu par Claude, outputs/, index.md, log.md, frontmatter standard, ouverture dans Obsidian. Utiliser quand l'utilisateur dit « crée mon vault », « organise mes notes », « installe le cerveau », « brique ». Pas pour la mémoire de Claude (utiliser memoire-fichiers) ni la recherche (utiliser recherche-par-le-sens)."
---
# Architecture du vault

## Pourquoi
Dans le système d'origine, tout ce qui entrait finissait au même endroit que ce que Claude écrivait. Résultat : on ne savait plus ce qui était une source brute et ce qui était une synthèse, et Claude réécrivait parfois l'original. La séparation en trois zones a réglé ça : ce qui entre (raw/, jamais modifié), ce que Claude tient à jour (wiki/), ce que Claude produit (outputs/). Le wiki a grandi jusqu'à plusieurs centaines de pages sans se perdre grâce à deux fichiers de navigation : index.md (le catalogue) et log.md (le journal).

## Prérequis
- Claude Code installé et ouvert dans le dossier choisi.
- Obsidian (gratuit) conseillé pour lire et voir le graphe. Optionnel : le vault reste du Markdown pur.
- Python 3.9 ou plus (pour les outils). Windows : `winget install Python.Python.3.12`. Mac : `brew install python`.
- Aucun coût.

## Interview
Lis d'abord : le dossier courant (`ls`), un éventuel `CLAUDE.md`, `wiki/maps/parcours.md`, tout dossier de notes existant. Si un vault existe déjà, propose de le garder et de compléter seulement ce qui manque.

Puis demande, une question à la fois :
Ce qui a déjà été répondu à l'installation (`wiki/maps/moi.md`, mémoire) ne se redemande pas.

1. « Où veux-tu que vive ton cerveau ? » (seulement si l'installation ne l'a pas fixé) Conseille un dossier hors des dossiers synchronisés par une app qui verrouille les fichiers la nuit, ou accepte un dossier synchronisé en sachant que les sauvegardes git s'en occupent (brique securite-git-secrets). Note le chemin.
2. « Tu as déjà des notes quelque part ? » (Notion, Google Docs, Apple Notes, Evernote, un dossier). Note la liste pour la brique d'ingestion qui correspond.
3. « Quels grands tiroirs pour ton activité ? » Propose par défaut : principes (ce que tu sais et enseignes), clients (une fiche par personne), sources (livres, auteurs, documents), contenu (ce que tu publies), strategie (offres, plan, décisions), maps (les cartes qui relient tout). Exemples d'adaptation : une boulangère ajoute « recettes » et « fournisseurs » ; un thérapeute garde « clients » privé.
4. « Y a-t-il des zones strictement privées ? » (argent, santé, famille). Elles iront dans `wiki/finances/` ou un dossier listé comme privé : aucun skill de contenu n'y touche.

Range les réponses dans `wiki/maps/architecture.md` (chemin, tiroirs, zones privées) et une ligne dans `log.md`.

## Construire
1. **Squelette (5 min).** Copie `.claude/skills/architecture-vault/outils/creer-vault.py` vers `scripts/creer-vault.py` du vault. Lance d'abord à blanc puis pour de vrai :
   ```bash
   python scripts/creer-vault.py . --dossiers principes,clients,sources,contenu,strategie,maps --essai
   python scripts/creer-vault.py . --dossiers principes,clients,sources,contenu,strategie,maps
   ```
   Il crée raw/, wiki/<tiroirs>/_index.md, outputs/, logs/, index.md, log.md, .gitignore. Il n'écrase jamais un fichier existant (il le liste « gardé »).
2. **Les règles du vault dans le cœur (5 min).** Ajoute au `CLAUDE.md` du vault (le cœur complet vient du bloc B, `CLAUDE.modele.md`) ce bloc court :
   ```markdown
   ## Règles du vault
   1. raw/ est immuable : Claude lit, ne modifie jamais, ne supprime jamais.
   2. wiki/ appartient à Claude : il crée, met à jour, relie, archive plutôt que supprimer.
   3. outputs/ reçoit tout ce qui est produit (brouillons, rapports, exports).
   4. Navigation : index.md, puis wiki/maps/, puis les pages, puis raw/ en dernier recours.
   5. Chaque page wiki porte le frontmatter standard et au moins 3 [[liens]].
   6. Zones privées (liste dans wiki/maps/architecture.md) : jamais lues par un skill de contenu.
   ```
3. **Frontmatter standard (2 min).** Toute page du wiki commence par :
   ```yaml
   ---
   title: "Titre lisible"
   type: principe | client | source | contenu | strategie | map | journal
   created: AAAA-MM-JJ
   updated: AAAA-MM-JJ
   tags: [mot1, mot2]
   sources: ["[[page-source]]"]
   ---
   ```
   Le champ `sources` relie chaque affirmation à son origine. Le jardinier complète les clés manquantes la nuit, sans écraser.
4. **Journal (2 min).** Format d'une entrée de `log.md`, une par session, dates absolues :
   ```markdown
   ## [AAAA-MM-JJ] type | ce qui a été fait
   - pages créées : [[a]], [[b]]
   - reste à faire : ...
   ```
   Le titre `## [AAAA-MM-JJ]` est obligatoire : le jardinier s'en sert pour archiver par trimestre.
5. **Cartes de départ (5 min).** Copie `parcours/parcours-modele.md` vers `wiki/maps/parcours.md` et `parcours/routage-modele.md` vers `wiki/maps/routage.md` si ce n'est pas déjà fait. Écris `wiki/maps/architecture.md` avec les réponses de l'interview.
6. **Obsidian (5 min, ses mains).** Guide-le : ouvrir Obsidian, « Ouvrir un dossier comme coffre », choisir le dossier du vault. Puis Réglages > Fichiers et liens : « Nouveau lien » = « Chemin le plus court », « Toujours mettre à jour les liens internes » activé. Réglages > Fichiers et liens > Fichiers exclus : ajouter `outputs/` et `raw/` pour garder le graphe lisible.
7. **Git local (2 min).** `git init` puis un premier commit. Le dépôt GitHub privé vient avec securite-git-secrets.

Variantes : sous Windows les commandes Python marchent telles quelles dans PowerShell ou Git Bash. Sur Mac remplace `python` par `python3` si besoin.

## Test
`python scripts/creer-vault.py . --essai` affiche « Créés : 0 » (tout est en place). Le contrôle des liens se repasse plus tard avec `lint-wiki`.

## Pièges vécus
- Claude a parfois « corrigé » un fichier de raw/. Depuis, la règle 1 est dans le cœur et le hook anti-suppression bloque les destructions. Un miroir tenu par un script (raw/notion-sync/, raw/appels/) est la seule exception : seul son script l'écrit.
- Des liens écrits avec des noms de page approximatifs ont produit plus d'un millier de liens morts. Règle : vérifier qu'une page existe avant de la lier, et laisser lint-wiki et le jardinier attraper le reste.
- Dates relatives (« hier », « jeudi ») dans le journal : illisibles un mois plus tard. Toujours AAAA-MM-JJ.
- Noms de fichiers avec accents et espaces : cassent certains scripts. Préfère `mots-en-tirets.md` en minuscules.

## Entretien dans le temps
Le jardinier (brique jardinier) maintient frontmatter, index et journal chaque nuit. lint-wiki fait un bilan hebdomadaire. Quand un tiroir dépasse une centaine de pages, crée des sous-cartes dans wiki/maps/.

## Après
Coche la ligne `architecture-vault` dans `wiki/maps/parcours.md`, ajoute une entrée dans `log.md`, puis propose securite-git-secrets (le filet de sécurité avant d'écrire beaucoup).
