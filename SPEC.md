# SPEC du repo « machine-claude » (contrat pour qui écrit ou met à jour ce repo)

## Ce qu'est ce repo
Une recette complète pour transformer un Claude Code ordinaire en bras droit d'entrepreneur : second cerveau, mémoire, experts, board, business piloté, machine à contenu, automatisations, apps. Elle vient d'un système réel construit pendant des mois par un coach entrepreneur (appelé ici « le système d'origine »). Elle doit marcher pour N'IMPORTE QUEL utilisateur et N'IMPORTE QUEL business : une mère, une sœur, un ami, un client qui l'achète.

L'utilisateur télécharge le zip, l'ouvre avec Claude Code et dit « installe ». Ensuite son Claude le guide du tout début jusqu'à la machine complète, et fait presque tout le travail lui-même.

## Les 4 lois du repo
1. **Interview d'abord, à chaque étape.** Aucune brique ne se construit avec des valeurs inventées. Chaque skill commence par une section « Interview » : les questions à poser à l'utilisateur (une à la fois ou en petit lot, langage simple), ce qu'on lit d'abord dans son vault pour ne pas redemander ce qu'on sait déjà, et où ranger les réponses. Le Claude de l'utilisateur adapte tout à ce qu'il sait de la personne.
2. **Claude fait le travail.** L'utilisateur ne fait que ce qui demande ses mains, ses accès (connexions, mots de passe, paiements) ou son accord. Tout le reste (écrire les fichiers, scripts, tâches planifiées, tests), Claude le fait.
3. **Zéro fuite.** Jamais : le nom du coach d'origine, sa marque, ses clients, ses chiffres, ses comptes, ses identifiants (IDs de notebooks, de comptes, de workflows), ses chemins de fichiers, ses secrets, ses auteurs de référence nommés comme « les siens ». On transmet la MÉCANIQUE et les LEÇONS, jamais le contenu. Exemples permis : « un notebook par expert de ton domaine (ex. pour un coach : les auteurs qu'il cite ; pour une boulangère : les livres de technique) ». Marques d'outils publics permises (Claude Code, Obsidian, NotebookLM, GitHub, Telegram, GoHighLevel, Linear, Fathom, etc.) en les présentant comme options. Seule exception : la vitrine publique signée par l'auteur (README.md, LICENSE, CONTRIBUTING.md, .github/, assets/) porte son nom, sa marque et son site ; aucune recette, aucun outil ne les reprend.
4. **Prouvé, pas théorique.** Chaque brique dit le problème qu'elle a réglé dans le système d'origine, ses pièges vécus et le test binaire qui prouve qu'elle marche.

## Arborescence
```
README.md                     pour l'humain : ce que c'est, comment démarrer (3 gestes)
LICENSE, CONTRIBUTING.md      licence MIT et guide de contribution (vitrine publique)
.github/ISSUE_TEMPLATE/       formulaires « demande » et « problème »
assets/                       images du README
INSTALLER.md                  pour Claude : le point d'entrée, l'ordre d'installation
CLAUDE.modele.md              le cœur à fusionner dans le CLAUDE.md de l'utilisateur
parcours/blueprint.md         la carte de toutes les briques, par bloc, dans l'ordre
parcours/parcours-modele.md   le tableau de suivi à copier dans wiki/maps/parcours.md
parcours/bloc-<x>.md          un fichier par bloc : liste de ses skills, ordre, dépendances
.claude/skills/<nom>/SKILL.md un skill par brique (recette) ; outils joints dans <nom>/outils/
.claude/commands/*.md         commandes courtes réutilisables
.claude/hooks/*.js            hooks génériques (Node, sans dépendance)
.claude/agents/*.md           sous-agents modèles (ex. client idéal)
outils/                       scripts génériques partagés (Python ou Node, sans dépendance cachée)
CHANGELOG.md                  ce qui a changé, daté
```

## Les blocs
- **A. Cerveau** : vault, architecture, mémoire, bibliothécaire, recherche par le sens, ingestion (fichiers, Drive, Notion, appels, réseaux), jardinier, lint, sécurité et sauvegardes.
- **B. Méthode et moteur Claude Code** : cœur CLAUDE.md, format de sortie, autonomie, hooks, settings, sous-agents et choix des modèles, skills et commandes (comment en créer), routage, passation/reprise, tâches (Linear ou autre), mods et apps locales, coûts et limites, Claude sans fenêtre (`claude -p`), jeton longue durée.
- **C. Experts** : NotebookLM branché (notebooklm-py), routage par carnet, comité (council, mode roast ancré), board des textes et sa porte, agent client idéal, contrôles de vérité et de voix, skills marketing.
- **D. Business** : entretien fondateur (mission, client idéal, offres, preuves), voix, plan unique et cockpit, fiches clients et dossiers, appels (enregistrement, analyse, objections), vente (offre, échelle, appel, préparation, débrief), CRM et messages, email, quiz et tunnels, pubs (seulement après le tunnel).
- **E. Machine à contenu** : banque d'idées, un sujet en plusieurs pièces, articles et SEO (avec leçon : la qualité bat la masse), posts, carrousels, Reels/Shorts et essais, YouTube (idées, miniatures, titres, scripts, tournage, montage), distribution, mesure et apprentissage.
- **F. Automatisation et pilotage** : tâches planifiées (Windows et Mac/Linux), journaux, gardien, notifications Telegram (urgent seulement + résumé), tâches de nuit, rapport du matin, scoreboard, journal et coach de vie, plan de la semaine.

## Format obligatoire d'un SKILL.md
```
---
name: <kebab-case, français>
description: "<ce que ça construit ou fait>. Utiliser quand l'utilisateur dit « … », « … ». <Pas pour … (utiliser …)>."
---
# <Titre>

## Pourquoi
Le problème réglé, vécu dans le système d'origine (2 à 4 phrases).

## Prérequis
Briques à avoir avant (noms de skills), outils, comptes, coût éventuel.

## Interview
Ce que tu lis d'abord dans son vault. Puis les questions, dans l'ordre, en langage simple. Où tu ranges chaque réponse.

## Construire
Étapes numérotées, chacune faisable en 20 minutes maximum. Pour chaque étape : ce que Claude fait, ce que l'utilisateur fait (en le guidant clic par clic quand c'est une interface), le fichier produit. Code ou gabarits complets quand c'est utile (scripts courts, sans dépendance cachée, avec gestion d'erreur). Variantes Windows ET Mac/Linux quand ça diffère.

## Test
Le critère binaire qui prouve que c'est fait.

## Pièges vécus
Les erreurs du système d'origine et comment les éviter.

## Entretien dans le temps
Comment la brique s'améliore ou se surveille ensuite (tâche planifiée, revue, mémoire).

## Après
Mettre à jour wiki/maps/parcours.md, log.md, la mémoire si une préférence est apparue, puis proposer la brique suivante.
```

## Style
Français simple, une idée par phrase, tutoiement de l'utilisateur dans les instructions qu'on lui lit, consignes à l'impératif pour Claude. Aucun tiret long (—, –). Pas de liste de trois en rythme, pas de « ce n'est pas X, c'est Y ». Zéro chiffre inventé : les chiffres du système d'origine sont permis seulement comme ordre de grandeur sans donnée privée (ex. « des dizaines de tâches planifiées »).
