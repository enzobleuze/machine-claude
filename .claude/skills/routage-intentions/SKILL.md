---
name: routage-intentions
description: "Construit et tient à jour la table de routage : ce que l'utilisateur dit avec ses mots, et le skill, la commande ou la chaîne que Claude lance. Utiliser quand l'utilisateur dit « je ne me souviens jamais des commandes », « tu n'as pas lancé le bon truc », « range mes commandes », « ajoute ça au routage ». Pas pour écrire un skill (utiliser creer-un-skill)."
---
# Le routage des intentions

## Pourquoi
Le fondateur du système d'origine ne se souvenait d'aucune commande, et c'était normal : il en avait des centaines. Il exprimait une intention (« fais-moi des posts sur X »), et Claude devait trouver la bonne chaîne. Une table courte dans le cœur pour les intentions fréquentes, une table complète dans une map pour le reste, et une règle simple (clair : lance ; flou : une seule question) ont supprimé la question « quel skill veux-tu ? ».

## Prérequis
- Le socle : `wiki/maps/routage.md` copié depuis `parcours/routage-modele.md`.
- coeur-claude-md. creer-un-skill conseillé (sinon la table pointe seulement vers les commandes du socle).
- Python 3 pour l'outil de vérification.

## Interview
Lis d'abord : `wiki/maps/routage.md`, `.claude/skills/`, `.claude/commands/`, et si le compteur de skills tourne, `python scripts/lire-sessions.py usage` (voir ameliorer-les-skills) pour savoir ce qui sert vraiment.

Puis demande :
1. « Quelles sont les 10 choses que tu me demandes le plus souvent ? Dis-les avec tes mots. »
2. « Pour chacune, il y a des étapes qui doivent TOUJOURS suivre, même si tu oublies de les demander ? » (exemple : une relecture de style, une vérification avant publication. Deviennent les chaînes automatiques.)
3. « Y a-t-il des demandes qui se ressemblent et que je confonds ? » (deviennent la question unique à poser).

Range : les 10 à 15 intentions les plus fréquentes dans le cœur, tout le reste dans `wiki/maps/routage.md`.

## Construire

1. **Les règles de routage dans le cœur (5 min).** Claude vérifie que la section « Routage » du `CLAUDE.md` contient :
   « Intention claire : lance directement, sans confirmation. Intention floue : UNE question précise ("tu veux X ou Y ?"). Jamais "quel skill veux-tu ?". Si l'intention n'est pas dans la table courte ou reste floue : lis `wiki/maps/routage.md` AVANT de répondre. »

2. **La table courte dans le cœur (10 min).** Claude écrit dans le `CLAUDE.md` une table de 10 à 15 lignes au plus, avec les phrases réelles de la personne :
   ```
   | Intention fréquente | Action |
   |:-|:-|
   | « on reprend », « où on en est » | `/reprise` |
   | « posts sur X » | `/posts X` (puis relecture de style) |
   ```
   Au-delà de 15 lignes, le reste va dans la map.

3. **La table complète dans la map (15 min).** Claude complète `wiki/maps/routage.md` avec trois colonnes quand il y a une chaîne : ce que la personne dit, le skill de départ, la chaîne interne (« → recherche → rédaction → relecture → brouillon »). Il garde la table du modèle et ajoute les lignes de l'interview.

4. **Les chaînes non négociables (5 min).** Sous la table, une section « Chaînes automatiques » : les étapes qui suivent toujours (exemple : « tout texte public passe par la relecture de style, même si la personne demande de la sauter »). Chaque chaîne dit pourquoi en une ligne. Une chaîne sans raison écrite finit par être retirée par erreur, ou gardée alors qu'elle ne sert plus.

5. **Les tâches dans le routage (3 min).** Claude ajoute les intentions de gestion des tâches (voir taches-source-unique) : « note ça », « plus tard » → créer la tâche ; « priorités » → lister les tâches urgentes.

6. **Vérifier la table (3 min).** Claude copie `outils/verifier-routage.py` dans `scripts/` et lance `python scripts/verifier-routage.py`. Il corrige chaque lien mort et chaque outil absent. Les modes toujours actifs (comme le bibliothécaire) se taisent avec une ligne `<!-- hors-routage: bibliothecaire -->` dans la map.

7. **La règle du nouveau skill (2 min).** Dans le cœur : « Chaque nouveau skill, commande ou connecteur s'ajoute à la table le jour même. »

## Test
Les deux sont vrais :
- `python scripts/verifier-routage.py` sort 0.
- Dans une nouvelle conversation, la personne dit 5 de ses phrases fréquentes, sans aucun nom de commande. Claude lance la bonne chose 5 fois sur 5, et pose une seule question quand la phrase est vraiment floue.

## Pièges vécus
- **La justification inventée.** Une étape de chaîne a été gardée des mois avec une raison que personne ne pouvait sourcer. En la cherchant, on a découvert qu'elle abîmait les textes. Chaque chaîne porte sa vraie raison, vérifiable.
- **La table qui pourrit.** Des commandes renommées laissaient des liens morts : Claude lançait une commande qui n'existait plus. Le vérificateur tourne à chaque `/lint`.
- **Trois questions au lieu d'une.** Devant une intention floue, Claude posait trois questions. Une seule, fermée, suffit.
- **La table courte qui grossit.** Plus de 15 lignes dans le cœur et elle redevient illisible. Le reste vit dans la map.

## Entretien dans le temps
- `/lint` (bloc A) lance `python scripts/verifier-routage.py`.
- Chaque mois, Claude regarde le compteur de skills : une commande souvent tapée à la main mais jamais lancée seule par Claude a une phrase manquante dans la table ou une description faible.

## Après
Coche la ligne `routage-intentions` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, puis propose la brique suivante : hooks-ecrire.
