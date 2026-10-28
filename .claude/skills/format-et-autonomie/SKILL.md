---
name: format-et-autonomie
description: "Règle la façon dont Claude rend ses comptes (TL;DR, AUTO, TOI, ALERTE) et quand il agit seul ou demande (règle des 95 %, plan validé, réfuter avant de présenter, ne pas cocher sans preuve). Utiliser quand l'utilisateur dit « tes réponses sont trop longues », « tu me demandes tout le temps », « tu fais des choses sans demander », « je ne comprends pas tes rapports ». Pas pour la longueur du CLAUDE.md (utiliser coeur-claude-md)."
---
# Format de sortie et autonomie

## Pourquoi
Dans le système d'origine, deux plaintes revenaient. D'abord les rapports trop longs, écrits dans un français trop dense, que l'entrepreneur devait relire deux fois. Ensuite un balancier : soit Claude partait sur des suppositions silencieuses, soit il demandait « je lance ? » à chaque étape d'un plan déjà validé. Un format fixe en quatre cases et des règles claires sur quand demander ont réglé les deux.

## Prérequis
- coeur-claude-md fait (le cœur contient déjà les sections « Format » et « Autonomie » du modèle).
- Aucun outil, aucun coût.

## Interview
Lis d'abord : les sections « Format de tes réponses », « Vérifier avant de livrer » et « Autonomie » du `CLAUDE.md`, les fichiers mémoire `feedback_*` qui parlent de longueur, de questions ou d'autonomie, `wiki/maps/moi.md` (niveau informatique, temps).

Puis demande, une question à la fois :
1. « Quand je finis une tâche, tu veux lire quoi en premier ? Le résultat, ce qui reste à faire pour toi, ou les risques ? » (ordre des cases si l'utilisateur veut le changer ; par défaut TL;DR, AUTO, TOI, ALERTE).
2. « Qu'est-ce que je ne dois JAMAIS faire sans ton accord ? » Propose la liste par défaut : ce qui est irréversible, ce qui coûte de l'argent, ce qui est publié ou envoyé, ce qui dépend de ton goût. Ajoute ce qu'il dit.
3. « Et qu'est-ce que tu veux que je fasse seul, même si je pourrais demander ? » (exemples : ranger le wiki, corriger une faute, relancer un script qui a planté).
4. « Combien de choses au maximum tu veux voir dans la case TOI ? » (par défaut 3, avec les minutes).
5. « Tu préfères que je pose toutes mes questions d'un coup avant un gros travail, ou une à une ? »

Range les réponses dans les sections du `CLAUDE.md` concernées et dans un fichier mémoire `feedback_autonomie.md` (Pourquoi + Comment l'appliquer).

## Construire

1. **Le format en quatre cases (10 min).** Claude vérifie que le cœur contient ce bloc, adapté aux réponses :
   ```
   **TL;DR** : 3 lignes maximum, le résultat d'abord.
   **AUTO** : ce que tu as fait toi-même.
   **TOI** : ce que <prénom> doit faire, 3 actions maximum, avec les minutes.
   **ALERTE** : le risque à connaître, sinon « rien ».
   ```
   Ajoute dessous : « Question simple : 1 à 3 phrases, sans les cases. » Sans cette ligne, Claude met des cases partout, même pour dire l'heure.

2. **Le français simple (5 min).** Dans le cœur : « Une idée par phrase. Mots de tous les jours. Un mot technique s'explique en 5 mots la première fois. Listes de 5 points maximum. » Test : la personne comprend du premier coup, fatiguée, entre deux tâches.

3. **La règle des 95 % (5 min).** Dans « Autonomie » : « Avant un gros travail (3 étapes ou plus, plusieurs fichiers, une décision d'architecture), pose toutes tes questions en une fois jusqu'à 95 % de confiance. Si tu te surprends à penser "je vais supposer X", c'est une question à poser. » Ne s'applique pas aux petites questions ni aux scripts déjà cadrés.

4. **Plan validé = feu vert (5 min).** Dans « Autonomie » : « Un plan ou une liste validé vaut accord pour toutes ses étapes. Tu enchaînes sans "je continue ?". Tu t'arrêtes seulement sur la liste de l'étape suivante. » Puis la liste de la question 2 de l'interview, mot pour mot.

5. **Ne pas cocher sans preuve (5 min).** Dans « Vérifier avant de livrer » : « Une étape n'est cochée que si tu es sûr à 95 % qu'elle est complète ET juste. Chaque liste de tâches contient ses étapes de vérification. Une seule tâche "en cours" à la fois, cochée dès qu'elle est finie, jamais en lot à la fin. »

6. **Réfuter avant de présenter (5 min).** Dans « Vérifier avant de livrer » : « Avant une recommandation à enjeu, essaie en silence de la casser (le cas où elle échoue). Montre seulement le bémol qui compte. Réflexe léger, jamais sur les petites questions. »

7. **Les fins vérifiables avec /goal (10 min, si la version de Claude Code le propose).** Claude tape `/goal` sans argument pour voir si la commande existe. Si oui, il ajoute une ligne au cœur : « Pour un travail dont la fin se prouve par une commande (un test qui passe, un rapport vide), utilise /goal avec la condition ET une borne : "… ou arrête-toi après 20 tours". Jamais pour un travail de goût (texte, image). » Sans borne, un goal mal posé mange la limite de la semaine.

8. **Le fichier mémoire (5 min).** Claude écrit `feedback_autonomie.md` dans la mémoire avec les réponses de l'interview, et une ligne dans `MEMORY.md`.

## Test
Les deux sont vrais :
- Claude donne à l'utilisateur une petite tâche réelle de 3 étapes déjà validées (par exemple : créer une page, la relier, l'ajouter à l'index). Claude l'enchaîne sans poser de question au milieu et finit avec les quatre cases, dont une case TOI de 3 lignes maximum.
- L'utilisateur pose une question simple (« quelle heure est-il à Tokyo ? ») : la réponse fait 1 à 3 phrases, sans les cases.

## Pièges vécus
- **Le « je lance ? » après chaque étape.** Il est apparu juste après l'ajout de règles de prudence. Il coûte un aller-retour et remet la personne en chef de projet. La règle « plan validé = feu vert » l'a arrêté.
- **La case TOI qui déborde.** Huit actions pour l'humain, c'est un aveu que Claude n'a pas fait son travail. Trois maximum, et Claude ne délègue jamais une micro-étape qu'il peut faire lui-même.
- **Les rapports en jargon.** Même la personne qui a construit le système devait se concentrer pour suivre. La règle « une idée par phrase » s'applique aux messages de Claude, pas seulement au contenu publié.
- **Cocher pour avancer.** Des tâches cochées « faites » sans test ont caché des scripts cassés pendant des semaines. Pas de coche sans preuve.
- **Les erreurs dramatisées.** Une erreur s'annonce sobrement, avec ce qui est fait pour la réparer. Pas d'excuses en trois paragraphes.

## Entretien dans le temps
- Chaque fois que l'utilisateur dit « trop long », « je ne comprends pas » ou « tu aurais dû demander », Claude met à jour `feedback_autonomie.md` le jour même.
- Une fois par mois, Claude relit ses 10 derniers rapports de fin de tâche (dans les transcriptions, voir ameliorer-les-skills) et vérifie qu'ils respectent les quatre cases.

## Après
Coche la ligne `format-et-autonomie` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, la mémoire est déjà faite, puis propose la brique suivante : passation-reprise.
