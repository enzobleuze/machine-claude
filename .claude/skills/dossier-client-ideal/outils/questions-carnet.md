# Questions pour les carnets NotebookLM

Une question par fichier, amorce comprise. Lancer : `python scripts/nlm_ask.py ask <clé du carnet> <fichier>`. Chaque phrase rendue garde la source que le carnet cite. Une réponse sans source citée ne rentre pas dans le dossier.

## L'amorce (à mettre en tête de chaque fichier)

```
Réponds UNIQUEMENT depuis les sources de ce carnet. Pour chaque point, cite la phrase exacte, mot pour mot, entre guillemets, et le titre de la source. N'invente rien, ne reformule pas. Si les sources ne disent rien sur un point, écris « rien dans les sources ».
```

## Carnet voix-client : une catégorie par fichier

1. **Douleurs.** « Quelles sont les situations concrètes que les clients décrivent comme les plus douloureuses ? Donne 15 phrases exactes, les plus fréquentes d'abord, avec la source. »
2. **Peurs.** « De quoi les clients disent-ils avoir le plus peur ? Donne 10 phrases exactes avec la source. »
3. **Désirs.** « Qu'est-ce que les clients disent vouloir ? Regroupe les phrases qui veulent dire la même chose, compte combien de sources différentes disent chaque désir, et donne une phrase exacte par désir. »
4. **Rêves.** « Comment les clients décrivent-ils leur vie une fois le problème réglé, au-delà du problème lui-même ? Donne 10 phrases exactes avec la source. »
5. **Déjà essayé.** « Qu'est-ce que les clients ont déjà essayé avant de demander de l'aide, et qu'est-ce que ça a donné selon eux ? Donne chaque tentative avec la phrase exacte et la source. »
6. **Mythes.** « Quelles croyances générales sur le problème les clients répètent-ils, du genre « on dit que », « tout le monde sait que », « normalement » ? Donne les phrases exactes et la source. »
7. **Fausses solutions.** « Qu'est-ce que les clients pensaient devoir faire pour s'en sortir ? Donne les phrases exactes avec la source. »
8. **Ce qu'ils ne veulent plus être.** « Comment les clients décrivent-ils la personne qu'ils sont devenus et qu'ils ne veulent plus être ? Phrases exactes et source. »
9. **Objections.** « Qu'est-ce qui a fait hésiter les clients avant d'acheter ou de réserver : prix, peur, méfiance, temps ? Phrases exactes et source. »
10. **Le déclic.** « Qu'est-ce qui a poussé les clients à demander de l'aide CE jour-là ? Phrases exactes et source. »
11. **Pensées secrètes.** « Quelles pensées intérieures les clients avouent-ils, celles qui commencent par « je me dis », « j'ai l'impression », « et si » ? Phrases exactes et source. »
12. **En cachette.** « Quels gestes les clients avouent-ils faire sans le dire à personne : vérifier, éviter, compenser ? Phrases exactes et source. »
13. **Micro-moments.** « Donne 10 scènes précises racontées par les clients : le lieu, l'heure, ce qui s'est passé, et ce qu'ils se sont dit à ce moment-là. Phrases exactes et source. »

Pour creuser une situation précise, ajoute à la question : « Seulement quand le client parle de <situation> ».

## Carnet de l'expert qui fait foi : trancher les mythes

Un seul fichier, avec la liste numérotée des sections 6 et 7 du dossier :

```
Voici des croyances de mes clients, numérotées. Pour CHAQUE numéro : VRAI, FAUX ou NUANCE selon tes sources, une phrase qui explique, la phrase exacte de la source qui le montre, et le titre de la source.
1. « <croyance> »
2. « <croyance> »
```

Seules les réponses FAUX ou NUANCE avec une source citée remplissent la ligne « Vrai : » du dossier. Une croyance que l'expert juge VRAIE sort de la liste des mythes.

## Sans carnet

Les mêmes 13 questions se posent au vault avec la recherche par le sens : `python scripts/cerveau.py "<question reformulée>"`, deux ou trois reformulations par question, puis lecture des notes trouvées pour copier les phrases exactes.
