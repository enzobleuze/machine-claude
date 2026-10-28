---
title: "Blueprint Machine Claude : la carte de toutes les briques"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [machine, blueprint, parcours]
sources: ["[[parcours]]", "[[routage]]", "[[index]]"]
---
# Blueprint Machine Claude

La carte du système complet, dans l'ordre où il se construit. Chaque bloc a son fichier (`bloc-a.md` à `bloc-f.md`) qui liste ses briques, et chaque brique a son skill dans `.claude/skills/`. Le suivi vit dans [[parcours]], la table des commandes dans [[routage]].

## Règles du parcours
- **L'ordre compte.** Les fondations d'abord, l'automatisation en dernier : une brique automatisée sur une base fausse automatise l'erreur.
- **Le business passe avant l'outillage.** Dès le bloc D, au moins la moitié du temps va à servir et vendre, pas à construire. Chaque plan de semaine contient des actions de vente.
- **Interview à chaque brique.** Le skill de la brique dit quoi lire d'abord et quoi demander. Ce qui est déjà su ne se redemande pas.
- **20 minutes maximum par étape.** Une brique peut prendre plusieurs séances.
- **Ce qui existe et marche est coché, jamais refait.**
- **Une brique est finie quand son test passe.**

## Les blocs, dans l'ordre
| Bloc | Fichier | Ce qu'il construit | Quand le commencer |
|:-|:-|:-|:-|
| 0. Audit | INSTALLER.md, étape 7 | l'état de départ | tout de suite |
| A. Cerveau | `bloc-a.md` | vault, mémoire, bibliothécaire, recherche par le sens, ingestion, jardinier, sauvegardes | après l'audit |
| B. Méthode | `bloc-b.md` | cœur, format, autonomie, hooks, sous-agents, skills, routage, tâches, apps, coûts, Claude sans fenêtre | en parallèle de A dès que le vault existe |
| C. Experts | `bloc-c.md` | carnets NotebookLM, comité, board des textes, client idéal, contrôles de vérité et de voix | quand `architecture-vault`, `memoire-fichiers` et `recherche-par-le-sens` passent |
| D. Business | `bloc-d.md` | entretien fondateur, voix, plan unique, clients, appels, vente, cockpit, CRM, email, tunnel, pubs | l'entretien fondateur peut commencer dès la première semaine |
| E. Contenu | `bloc-e.md` | idées, un sujet en pièces, articles, posts, carrousels, Reels, YouTube, distribution, mesure | après `entretien-fondateur` et `board-textes` |
| F. Automatisation | `bloc-f.md` | tâches planifiées, gardien, notifications, nuit, matin, dimanche, journal, revue de vie | une brique à la fois, seulement sur ce qui marche déjà à la main |

Raccourci conseillé pour un débutant : `architecture-vault`, `securite-git-secrets`, `memoire-fichiers`, `bibliothecaire-installer`, `coeur-claude-md`, `passation-reprise`, `entretien-fondateur`, `plan-unique`, puis le reste selon ses priorités. Les briques se désignent toujours par le nom de leur skill ; leur numéro vit seulement dans [[parcours]].

## Les leçons apprises à la dure (à ne jamais refaire)
1. **Outiller avant de vendre.** Des mois de construction sans revenu. Le système sert le business, jamais l'inverse.
2. **Plusieurs plans qui se contredisent.** Un seul plan vivant, avec une ligne PROCHAINE.
3. **Des plans géants.** Ils font geler. Des planchers de 20 minutes.
4. **Produire en masse.** Des dizaines d'articles générés automatiquement n'ont presque rien rapporté. Peu, vrai, utile, écrit pour une vraie personne.
5. **Les pubs avant un parcours client complet.** De l'argent perdu. L'organique et le tunnel d'abord.
6. **Une règle notée seulement dans le wiki est oubliée.** Une règle critique vit dans le CLAUDE.md, un script ou un hook qui la fait respecter.
7. **Un outil qui « embellit » les textes peut inventer** (il a ajouté de fausses études chiffrées). Chaque chiffre se vérifie par la source, les règles de style par un script.
8. **Une question globale à un expert laisse passer des erreurs.** Le board juge affirmation par affirmation.
9. **Les agents IA installés d'office dans un outil** (CRM, réseaux) ont créé de faux brouillons. Tout agent est vérifié avant d'être allumé.
10. **Trop de notifications** et on n'en lit plus aucune. Seul l'urgent sonne, le reste va au résumé.
11. **Des dizaines de passations sans état unique** : on tourne en rond. Un plan, un parcours, un log.
12. **Après chaque ajout** (une source, un outil, une règle), se demander : faut-il un skill ? un souvenir ? un hook ? supprimer l'ancien ? changer un prompt ?

## Ce qui ne se copie pas
Les idées, la voix, les clients, les chiffres et les comptes du système d'origine. On reprend la mécanique. Le contenu vient de la personne, de ses clients et de ses sources.
