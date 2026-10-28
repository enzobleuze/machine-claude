---
name: coeur-claude-md
description: "Construit le cœur CLAUDE.md court (règles chargées à chaque session) et les maps chargées à la demande dans wiki/maps/. Utiliser quand l'utilisateur dit « mon CLAUDE.md est trop long », « Claude oublie mes règles », « range mes règles », « installe le cœur ». Pas pour le format des réponses (utiliser format-et-autonomie) ni pour la table des commandes (utiliser routage-intentions)."
---
# Le cœur CLAUDE.md et les maps à la demande

## Pourquoi
Dans le système d'origine, le CLAUDE.md a grossi jusqu'à plusieurs centaines de lignes. Chaque session et chaque appel automatique le relisait en entier : des jetons payés pour rien, et des règles importantes noyées au milieu de détails. La solution a été un cœur court (moins de 260 lignes) qui contient seulement ce qui doit vivre à chaque tour, plus des pages « maps » que Claude lit quand un déclencheur le demande. Depuis, les règles dures sont respectées et le coût fixe de chaque appel a baissé.

## Prérequis
- Le socle installé : `CLAUDE.modele.md` fusionné dans le `CLAUDE.md` du vault (voir `INSTALLER.md`).
- Un vault avec `wiki/maps/` (bloc A).
- Aucun coût.

## Interview
Lis d'abord : le `CLAUDE.md` actuel, `CLAUDE.avant-machine.md` s'il existe, `MEMORY.md` et les fichiers mémoire `feedback_*`, `wiki/maps/moi.md`. Note ce qui est déjà une règle pour ne pas la redemander.

Puis pose ces questions, une à la fois :
1. « Quelles sont les erreurs de Claude qui t'énervent au point de vouloir une règle qui ne se discute pas ? » (deviennent les règles dures, section « Règles dures »).
2. « Qu'est-ce qui passe avant tout le reste quand tu produis quelque chose ? » (confirme ou ajuste la hiérarchie des priorités du modèle).
3. « Y a-t-il des mots, des tournures ou des sujets interdits dans ce que tu publies ? » (règles dures de style, ou une map `regles-qualite.md` si la liste dépasse 10 lignes).
4. « Quels gros sujets reviennent souvent et demandent beaucoup de détail ? » (chacun devient une map avec son déclencheur).
5. « Y a-t-il des zones privées en plus de finances et clients ? » (section « Zones privées »).

Range : règles dures et priorités dans `CLAUDE.md`, détail dans `wiki/maps/<sujet>.md`, chaque préférence nouvelle dans un fichier mémoire `feedback_<sujet>.md`.

## Construire

1. **Mesurer (5 min).** Claude compte les lignes : `wc -l CLAUDE.md` (Mac/Linux, Git Bash) ou `(Get-Content CLAUDE.md).Count` (PowerShell). Au-dessus de 260, on passe à l'étape 2. Fichier produit : aucun.

2. **Trier chaque section (20 min).** Claude classe chaque bloc du CLAUDE.md dans une de ces trois cases, et montre le tableau à l'utilisateur :
   | Case | Critère | Destination |
   |:-|:-|:-|
   | Cœur | doit agir à chaque tour, même sur une petite question | reste dans CLAUDE.md |
   | Map | utile seulement pour un type de travail | `wiki/maps/<sujet>.md` + une ligne déclencheur dans CLAUDE.md |
   | Mémoire | préférence ou fait sur la personne | fichier mémoire, une ligne dans MEMORY.md |
   L'utilisateur valide le tableau en une fois.

3. **Écrire les maps (20 min par lot de 3).** Claude crée chaque map avec un frontmatter (`title`, `type: map`, `created`, `updated`, `tags`, `sources`) et au moins 3 [[liens]]. Il recopie le détail sans le résumer : rien ne se perd.

4. **Poser les déclencheurs (10 min).** Dans CLAUDE.md, chaque map gagne une ligne de la forme :
   `- Avant de toucher à <sujet> : lis [[wiki/maps/<sujet>]].`
   Ou une table « Sujet | Map à lire AVANT » quand il y en a plus de 5. Le mot qui compte est AVANT : Claude lit la map avant d'agir, pas après une erreur.

5. **Garder une archive (5 min).** Avant de raccourcir, Claude copie la version longue dans `wiki/maps/archive/claude-md-<date>.md` et y renvoie en bas du cœur. Rien n'est jamais perdu.

6. **Ajouter le garde-fou de taille (5 min).** Une ligne dans le cœur : « Ce fichier reste sous 260 lignes ; le détail va dans wiki/maps/. » Et une ligne dans `MEMORY.md` : « Index sous 45 lignes, le détail dans les fichiers. » (La mémoire automatique est tronquée au-delà d'une certaine taille : un index trop long perd ses dernières lignes en silence.)

7. **Règle par règle, l'exemple qui tue (10 min).** Pour chaque règle dure, Claude ajoute un exemple interdit court entre parenthèses (« ❌ … »). Une règle sans exemple se comprend de travers.

### Gabarit d'une map
```markdown
---
title: "<Sujet> : tout le détail"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [<sujet>]
sources: ["[[CLAUDE]]"]
---
# <Sujet>
> Quand lire : avant <type de travail>. Lien depuis le cœur : section <x>.

## Règles
## Comment faire
## Pièges déjà payés
## Liens
[[index]] · [[routage]] · [[<page voisine>]]
```

## Test
Les trois sont vrais :
- `CLAUDE.md` fait moins de 260 lignes.
- Chaque map citée dans CLAUDE.md existe (Claude vérifie chaque [[lien]] avec Glob).
- Dans une nouvelle conversation, l'utilisateur pose une question qui touche une map (par exemple « écris un post ») : Claude dit lire la map avant d'écrire.

## Pièges vécus
- **Le cœur qui regrossit.** Chaque session ajoute « juste une ligne ». Le garde-fou de taille et le passage mensuel de l'étape 1 l'arrêtent.
- **Règles en double.** Une règle écrite dans le cœur ET dans une map finit par diverger. Une règle vit à un seul endroit ; l'autre endroit pointe vers elle.
- **Les tâches automatiques ne lisent pas les maps.** Un appel `claude -p` sans outil de lecture ne suit pas un lien. Les règles critiques pour la nuit doivent être copiées dans le prompt du script (voir claude-sans-fenetre).
- **Un wiki passif n'agit pas.** Une règle rangée dans une map sans déclencheur dans le cœur est oubliée. Toute règle critique a sa ligne déclencheur, un hook, ou les deux.
- **Les placeholders oubliés.** Un `{{PRENOM}}` resté dans le cœur rend Claude confus. Claude cherche `{{` avant de finir.

## Entretien dans le temps
- Une fois par mois (ou pendant `/lint`), Claude recompte les lignes et propose de sortir ce qui a regrossi.
- Chaque fois qu'une règle est violée deux fois, Claude propose de la monter d'un cran : map → cœur, cœur → hook.

## Après
Coche la ligne `coeur-claude-md` dans `wiki/maps/parcours.md`, écris une ligne dans `log.md`, crée un fichier mémoire si une préférence est apparue, puis propose la brique suivante : format-et-autonomie.
