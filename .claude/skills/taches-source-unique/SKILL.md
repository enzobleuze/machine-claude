---
name: taches-source-unique
description: "Installe une source unique pour les tâches (Linear par connecteur MCP, un autre outil, ou un simple fichier) avec création immédiate et définition de fini, le parking à idées, la revue mensuelle et la limite de 2 chantiers. Utiliser quand l'utilisateur dit « mes idées se perdent », « où on en est », « note ça pour plus tard », « j'ai trop de choses en cours », « branche Linear ». Pas pour le plan stratégique (bloc D) ni les rappels personnels du téléphone."
---
# Une source unique pour les tâches

## Pourquoi
Dans le système d'origine, les tâches vivaient à cinq endroits : la liste de la session, la mémoire, des fichiers de notes, le journal, une appli de rappels. Aucun ne permettait à Claude de répondre à « où on en est ? ». Les « on verra plus tard » mouraient. Une seule source pour les tâches, branchée à Claude par un connecteur, avec un gabarit qui force une définition de fini, a réglé le problème. Le parking à idées a ensuite protégé la liste : une idée qui peut attendre un an n'encombre plus les tâches.

## Prérequis
- format-et-autonomie, passation-reprise.
- Le socle : commande `/idee` (parking dans `wiki/maps/parking.md`).
- Un outil de tâches au choix (voir Interview). Linear a une offre gratuite limitée en nombre de tâches actives ; un fichier ne coûte rien.

## Interview
Lis d'abord : `wiki/maps/parking.md`, `log.md`, la mémoire (tâches rangées au mauvais endroit ?), les connecteurs déjà branchés (`claude mcp list` ou `/mcp`).

Puis demande :
1. « Où sont tes tâches aujourd'hui ? » (appli, papier, tête, plusieurs endroits).
2. « Tu veux un vrai outil de tâches, ou un simple fichier dans ton vault ? » Présente les options en une ligne chacune :
   - Linear (connecteur MCP officiel, gratuit avec une limite de tâches actives, appli téléphone) ;
   - un autre outil qui a un connecteur MCP (Todoist, Notion, Plane, Asana…) ;
   - un fichier `wiki/maps/taches.md` (zéro installation, mais pas de téléphone ni de rappels).
3. « Tes rappels personnels (courses, rendez-vous) vont-ils dans le même outil ? » Conseil : non, une appli de rappels à part ; l'outil de tâches garde le travail.
4. « Quelles grandes familles de travail ? » (deviennent 5 à 8 étiquettes ; exemple : contenu, vente, technique, offre, perso, finance, entretien du wiki).
5. « Combien de chantiers tu peux porter en même temps sans te noyer ? » (par défaut 2).

Range : le choix et les étiquettes dans `wiki/maps/taches-workflow.md`, la règle des chantiers dans le cœur.

## Construire

1. **La règle de partage (5 min).** Claude écrit dans le cœur :
   « Tâches = <outil choisi>. Connaissance = le wiki. Préférences et façons de travailler = la mémoire. Rien en double. Jamais une tâche dans la mémoire ou le journal. »

2. **Brancher l'outil (15 min).**
   - Linear : la personne crée un compte et un espace (Claude la guide écran par écran). Puis le branchement par clé personnelle, qui n'expire pas :
     1. Dans Linear, la personne ouvre les réglages de son compte, rubrique « Security & access », partie « Personal API keys », crée une clé nommée « Claude » et la copie. Si l'écran a changé, Claude cherche le chemin sur la page d'aide de Linear (« personal API key »).
     2. Elle ouvre un terminal (jamais la conversation) et colle la ligne que Claude lui prépare, `<clé>` remplacé par sa clé : `claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp --header "Authorization: Bearer <clé>"`. La clé ne passe jamais dans la conversation.
     3. Elle redémarre Claude. Claude vérifie qu'il voit l'espace (il liste les équipes), puis crée les étiquettes de l'interview.
     Plan B, si la clé coince : `claude mcp add --transport http --scope user linear https://mcp.linear.app/mcp`, puis `/mcp` ; la personne clique « autoriser » dans son navigateur. Vérifie l'adresse sur la page officielle « MCP » de Linear.
   - Autre outil : même geste avec son connecteur (voir connecteurs-mcp).
   - Fichier : Claude crée `wiki/maps/taches.md` avec quatre sections « En cours », « À faire », « Plus tard », « Fait (30 derniers jours) » et 3 [[liens]].
   Test du branchement : Claude crée une tâche d'essai, la lit, puis l'annule.

3. **Le gabarit obligatoire (5 min).** Claude copie `outils/gabarit-tache.md` dans `wiki/maps/taches-workflow.md` et ajoute au cœur : « Toute tâche suit ce gabarit. Une tâche sans définition de fini se complète avant d'agir. »

4. **Les cinq réflexes dans le cœur (10 min).** Claude écrit cette section, courte :
   1. Question floue (« où on en est », « priorités ») : lire les tâches urgentes et hautes AVANT de répondre, en montrer 5, demander lesquelles on attaque.
   2. « Plus tard », « note ça », « il faudra » (dit par la personne OU par Claude) : créer la tâche tout de suite, avec le gabarit, et montrer son identifiant. Jamais un « plus tard » sans tâche. Si l'idée peut attendre des mois : `/idee` à la place.
   3. Sujet concret mentionné : chercher les tâches existantes sur ce sujet avant de proposer du neuf.
   4. Début d'une vraie session : lire en silence les tâches en cours.
   5. Fin de session : mettre à jour l'état des tâches touchées (fait, en cours avec un commentaire, annulé avec la raison).

5. **Les chantiers (3 min).** Dans le cœur : « Au plus <N> chantiers en même temps. Un travail hors du plan : le dire en une ligne et proposer `/idee`. » Un chantier est une grosse tâche ouverte (taille L ou XL en cours).

6. **Le parking à idées (5 min).** Claude vérifie que `wiki/maps/parking.md` existe (créé par `/idee`), avec une section « À trier » en haut, vide en fin de session : Claude range chaque idée dans une section thématique pendant `/fin`. Format d'une ligne : `- AAAA-MM-JJ [source] texte court.`

7. **La revue mensuelle (5 min).** Claude ajoute à `wiki/maps/taches-workflow.md` : « Le 1er du mois : Claude propose 10 idées du parking à promouvoir en tâches (avec le gabarit) ou à tuer (section "Tuées", avec la date). La personne décide. » Si l'outil a une limite de tâches actives, la revue sert aussi de filtre : une tâche qui n'est pas faisable dans les 3 mois retourne au parking.

8. **Le routage (2 min).** Les phrases de la personne vont dans `wiki/maps/routage.md` (« note ça », « priorités », « qu'est-ce qui reste », « explique-moi Linear »).

9. **La visite guidée (10 min).** Claude explique l'outil à la personne avec `outils/expliquer-linear.md` (pour un autre outil ou le fichier, même plan avec ses mots à lui) : à quoi il sert en deux phrases, les mots anglais de l'écran, les phrases à dire, ce que Claude fait seul, puis l'exercice sur le téléphone. Une idée, puis une pratique : jamais le texte d'un bloc. Claude copie ensuite le tableau « Ce que tu me dis » dans `wiki/maps/taches-workflow.md` pour le redonner à la demande.

## Test
Les trois sont vrais :
- Dans la conversation, la personne dit « il faudra refaire ma page d'accueil un jour ». Claude crée une tâche (ou une ligne de parking) sans qu'on le lui demande, avec une définition de fini, et montre où elle est.
- La personne dit « on en est où ? » : Claude liste 5 tâches réelles avant de répondre.
- La tâche d'essai de l'étape 2 a été créée puis annulée.
- Après la visite guidée, la personne dit avec ses mots à quoi lui sert l'outil, et retrouve sur son téléphone une tâche créée par Claude.

## Pièges vécus
- **Cinq listes, zéro vérité.** Tant que les tâches vivaient partout, personne ne savait l'état. Une seule source, et la règle de partage écrite dans le cœur.
- **La tâche floue.** « Améliorer le carrousel » est restée ouverte des semaines. La définition de fini testable l'aurait fermée en une session.
- **La liste qui déborde.** Avec des centaines de tâches, la liste ne veut plus rien dire. Le parking prend tout ce qui n'est pas faisable dans l'année.
- **La boîte « à trier » qui grossit.** Le parking marche seulement si Claude le range à chaque fin de session.
- **Le perso mêlé au travail.** Les rappels du téléphone noyaient les tâches de travail. Deux outils, deux usages.
- **Le connecteur branché par le navigateur a dû être reconnecté.** Quand l'autorisation tombe, Claude ne voit plus aucune tâche et la reprise se fait à l'aveugle. La clé personnelle n'expire pas : elle est devenue le branchement par défaut. Elle se garde comme un mot de passe, car elle donne accès à tout l'espace.
- **Une migration d'outil coûte cher.** Changer d'outil de tâches oblige à réécrire la reprise, la passation et les apps. Choisis une fois, et ne change que si une limite bloque vraiment.

## Entretien dans le temps
- Chaque fin de session : réflexe 5.
- Chaque 1er du mois : la revue de l'étape 7.
- Chaque trimestre : archiver les tâches finies ou mortes.

## Après
Coche la ligne `taches-source-unique` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, puis propose la brique suivante : routage-intentions.
