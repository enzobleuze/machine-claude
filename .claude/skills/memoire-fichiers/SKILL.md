---
name: memoire-fichiers
description: "Installe la mémoire de Claude en fichiers : un fichier court par leçon (préférence, projet, référence, profil), un index MEMORY.md court lu à chaque conversation, des archives mensuelles. Utiliser quand l'utilisateur dit « souviens-toi de ça », « tu oublies tout d'une session à l'autre », « installe la mémoire », « brique ». Pas pour ranger des connaissances métier (elles vont dans le wiki, voir architecture-vault)."
---
# Mémoire en fichiers

## Pourquoi
Dans le système d'origine, le fondateur répétait les mêmes corrections de session en session : Claude lisait une règle, disait « super », puis l'oubliait à la conversation suivante. La cause : une règle rangée dans le wiki n'est lue que si on l'ouvre. La mémoire en fichiers a réglé ça, car Claude Code charge automatiquement l'index `MEMORY.md` au début de chaque conversation. Deuxième leçon : cet index est tronqué au-delà d'une certaine taille, donc il doit rester court, et le détail vit dans les fichiers.

## Prérequis
- architecture-vault fait.
- Claude Code récent (mémoire automatique par projet). Aucun coût.

## Interview
Lis d'abord : le dossier mémoire du projet (voir étape 1), `wiki/maps/architecture.md`, les dix dernières entrées de `log.md`. Ne redemande pas ce qui y est.

Puis demande :
1. « Comment veux-tu que je t'appelle, et qu'est-ce que je dois savoir de toi pour bien t'aider ? » (métier, rythme, contraintes de temps). Va dans `user_profil.md`.
2. « Qu'est-ce qui t'agace le plus quand une IA t'aide ? » Chaque réponse devient un fichier `feedback_*.md`.
3. « Quel est ton chantier principal en ce moment ? » Va dans `project_<chantier>.md`.
4. « Tu préfères des réponses courtes ou détaillées ? Tutoiement ? » Va dans `feedback_format.md`.

## Construire
1. **Trouver le dossier (2 min).** Claude Code range la mémoire du projet sous `~/.claude/projects/<chemin du projet avec les caractères spéciaux remplacés par des tirets>/memory/`. Windows : `%USERPROFILE%\.claude\projects\C--Users-...\memory\`. Mac : `~/.claude/projects/-Users-.../memory/`. Crée-le s'il manque. Il vit hors du vault : c'est voulu (il contient des préférences personnelles), la brique sauvegardes-3-lieux le copie dans le coffre chiffré.
2. **Les quatre types (5 min).** Un fichier par leçon, nommé `<type>_<sujet>_<AAAA-MM-JJ>.md` :
   - `user` : qui est la personne (profil, contraintes, façon de penser).
   - `feedback` : une correction ou une préférence (« ne fais plus X », « fais toujours Y »).
   - `project` : l'état d'un chantier ou d'une décision business.
   - `reference` : où trouver quoi (outil installé, emplacement d'une clé, identifiant d'un service).
   Gabarit obligatoire :
   ```markdown
   ---
   name: feedback-reponses-courtes-2026-01-15
   description: "Réponses de 10 lignes max, une idée par phrase."
   type: feedback
   ---
   La règle en une phrase.

   **Why:** ce qui s'est passé, avec la phrase exacte de la personne si possible.
   **How to apply:** quand et comment l'appliquer, ce qui reste permis.
   ```
   Le « Why » permet de juger les cas limites. Sans lui, Claude applique la règle de travers.
3. **L'index court (5 min).** `MEMORY.md` = une ligne par fichier, en trois sections :
   ```markdown
   ## Actifs
   - [Chantier site web (15/01)](project_site_web_2026_01_15.md) : refonte en cours, livraison fin du mois.
   ## Comportement permanent
   - [Réponses courtes (15/01)](feedback_reponses_courtes_2026_01_15.md) : 10 lignes max.
   ## Archives
   - [Archive 2026-01](archive/2026-01.md) : entrées closes de janvier.
   ```
   Limites : environ 45 lignes, moins de 200 caractères par ligne. Le crochet de la ligne doit suffire à déclencher le bon réflexe.
4. **Règle d'écriture dans le cœur (3 min).** Ajoute au `CLAUDE.md` :
   ```markdown
   ## Mémoire
   Chaque correction ou préférence donnée en session devient tout de suite un fichier mémoire
   (règle + Why + How to apply) et une ligne dans MEMORY.md. Une règle critique pour une tâche
   automatique va AUSSI dans le prompt de cette tâche : la mémoire n'est pas lue sans conversation.
   ```
5. **Archives (5 min).** Quand l'index dépasse la limite : les entrées de chantiers finis passent dans `memory/archive/AAAA-MM.md` (une ligne chacune) et sortent de l'index. Les fichiers restent, rien n'est supprimé.
6. **Contrôle (2 min).** Copie `outils/memoire-check.py` vers `scripts/`, lance-le depuis la racine du vault :
   ```bash
   python scripts/memoire-check.py
   ```
   Il signale index trop long, lignes trop longues, liens morts, fichiers non indexés, frontmatter incomplet.
7. **Remplir (5 min).** Écris les fichiers issus de l'interview, puis relance le contrôle.

## Test
Ouvre une conversation neuve et demande « qu'est-ce que tu sais de moi et de mes préférences ? ». Claude répond avec le contenu des fichiers sans les ouvrir. Et `python scripts/memoire-check.py` sort « OK : mémoire saine. »

## Pièges vécus
- Règles rangées seulement dans le wiki : décoratives. La règle qui compte va dans la mémoire, et dans le prompt des tâches de nuit qui tournent sans conversation.
- Index qui gonfle jusqu'à la troncature : les dernières lignes disparaissaient sans bruit. D'où la limite et le contrôle.
- Fichiers mémoire longs comme des pages wiki : la mémoire dit le réflexe, le wiki garde le savoir.
- Deux fichiers qui se contredisent : quand une règle change, mets à jour l'ancien fichier (ou archive-le) au lieu d'en ajouter un second.

## Entretien dans le temps
Le jardinier peut lancer `memoire-check.py` une fois par mois et mettre le résultat dans son résumé. À chaque `/fin`, Claude ajoute les leçons du jour. Une fois par mois, archive les chantiers clos.

## Après
Coche la ligne `memoire-fichiers` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose bibliothecaire-installer.
