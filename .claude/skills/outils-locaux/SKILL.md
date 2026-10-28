---
name: outils-locaux
description: "Ajoute les outils qui tournent sur l'ordinateur : modèles d'IA locaux et gratuits pour le travail mécanique (trier, extraire, résumer en interne), et lignes de commande qui pilotent un site à la place des clics. Utiliser quand l'utilisateur dit « je veux économiser Claude », « un modèle gratuit sur mon PC », « ce clic dans le navigateur casse tout le temps », « automatise ce site sans API ». Pas pour un service qui a déjà un connecteur (utiliser connecteurs-mcp)."
---
# Outils locaux : modèles locaux et lignes de commande

## Pourquoi
Dans le système d'origine, deux familles de travail coûtaient cher pour peu de valeur. D'abord les tâches mécaniques (classer, extraire un champ, préparer une fiche) qui consommaient le forfait Claude. Ensuite les flux de navigateur (remplir un écran, publier dans une interface) qui cassaient à chaque changement de page et coûtaient des captures d'écran. Un modèle local gratuit a pris une partie du mécanique, avec repli automatique sur Claude. Une ligne de commande qui parle à l'API cachée derrière la page a remplacé les clics les plus fragiles.

## Prérequis
- couts-et-limites, claude-sans-fenetre.
- Pour les modèles locaux : un ordinateur avec assez de mémoire (une carte graphique aide beaucoup). Ollama (ollama.com) est gratuit.
- Python 3.

## Interview
Lis d'abord : `wiki/maps/couts.md`, `wiki/maps/automatisations.md`, `scripts/` (scripts de navigateur existants), `log.md` (flux qui cassent).

Puis demande :
1. « Quelle est ta machine ? » Claude vérifie lui-même si possible : mémoire vive, carte graphique et sa mémoire (Windows : `Get-CimInstance Win32_VideoController` ; Mac : menu Pomme, À propos de ce Mac ; Linux : `lspci` ou `nvidia-smi`).
2. « Quelles tâches répétitives et sans voix je fais pour toi ? » (classer, trier, extraire des champs, résumer des documents internes).
3. « Y a-t-il des données qui ne doivent jamais quitter ton ordinateur ? » (clients, santé, finances : le local est fait pour elles).
4. « Quels gestes dans un navigateur on refait chaque semaine, et lesquels cassent ? »

Range : les choix dans `wiki/maps/outils-locaux.md`.

## Construire

### A. Modèles locaux

1. **Installer Ollama (la personne, 10 min).** Guide le téléchargement sur ollama.com et l'installation. Claude vérifie : `ollama --version`.

2. **Choisir un ou deux modèles (10 min).** Claude regarde la mémoire de la carte graphique et choisit dans la bibliothèque d'Ollama (ollama.com/library) un modèle qui tient entièrement dedans : un petit modèle rapide pour trier et sortir du JSON, un moyen pour lire de longs textes. Règle de taille : le fichier du modèle doit être plus petit que la mémoire de la carte, sinon il ralentit très fort. Puis `ollama pull <modèle>`.

3. **Vérifier qu'il tourne sur la carte (3 min).** `ollama run <modèle> "dis bonjour"`, puis `ollama ps` : la colonne doit montrer le processeur graphique à 100 %. Sinon Ollama retombe en silence sur le processeur.

4. **Le client avec repli (5 min).** Claude copie `outils/modele-local.py` dans `scripts/`, lance `python scripts/modele-local.py --test`, puis un vrai essai : `python scripts/modele-local.py "Classe : vente, question ou autre. Un mot." --modele <modèle>`. Un script appelant traite le code 3 comme « repasse sur Claude ».

5. **La cascade (10 min).** Claude écrit dans `wiki/maps/outils-locaux.md` : le local trie, extrait et prépare ; Claude intervient si le local doute, si deux réponses ne concordent pas, ou si une règle dure saute. Il choisit UNE tâche de départ et mesure 20 cas : local contre Claude, côte à côte. La personne juge.

### B. Lignes de commande qui pilotent un site

6. **Le critère (5 min).** Un flux de navigateur mérite une ligne de commande quand deux de ces cas sont vrais : il revient chaque semaine ; il casse quand la page change ; il coûte des captures d'écran ; il demande une main de la personne. Ordre de préférence, du plus solide au plus fragile : API officielle, puis API interne que la page appelle déjà, puis script de navigateur (Playwright), puis pilotage par Claude dans le navigateur.

7. **Trouver l'API derrière la page (20 min).** Avec la personne connectée dans son navigateur, Claude ouvre les outils de développement (onglet Réseau, ou l'outil de lecture des requêtes de l'extension navigateur), refait le geste une fois, et repère la requête qui fait le travail. Il écrit un petit script dans `scripts/` qui rejoue cette requête, avec sortie `--json`, un `--test`, et un mode brouillon par défaut. Des projets libres (par exemple CLI-Anything) proposent une méthode et des gabarits pour cette étape : à lire en entier avant de l'installer, et sans installer de paquets tiers à la volée.

8. **Garder le secours (2 min).** Une API interne n'est pas officielle et peut changer du jour au lendemain. Le script garde le chemin d'avant (le script de navigateur ou l'étape manuelle) écrit dans sa fiche.

## Test
- Modèles locaux : `python scripts/modele-local.py --dispo` sort 0, et la mesure des 20 cas de l'étape 5 est notée dans `wiki/maps/outils-locaux.md` avec la décision.
- Ligne de commande : le script de l'étape 7 refait le geste en mode brouillon et sort 0 ; la personne voit le résultat dans le service.

## Pièges vécus
- **Le contexte coupé en silence.** Ollama coupe les longs textes à un petit contexte par défaut, sans erreur. Le client fixe le contexte et prévient quand le texte semble coupé.
- **Le processeur à la place de la carte.** Un modèle trop gros tombe sur le processeur et devient dix fois plus lent, sans message. `ollama ps` le montre.
- **Les modèles « :cloud ».** Certains noms de modèles d'Ollama finissent par `:cloud` : ils envoient les données dehors. Interdits pour le privé ; le client les refuse.
- **Les citations inventées.** Un modèle local invente parfois des phrases « exactes ». Jamais de citation sans contrôle par script contre le texte source, jamais un texte dans la voix de la personne.
- **Les offres gratuites en ligne qui ferment.** Plusieurs offres gratuites de modèles en ligne ont fermé en quelques semaines. Le local passe en premier.
- **Le compte Claude dans une passerelle.** Des passerelles qui réunissent plusieurs fournisseurs proposent de brancher l'abonnement Claude en se faisant passer pour Claude Code. C'est contraire aux conditions d'utilisation : risque de suspension du compte qui fait tourner tout le système. Jamais.
- **Le mot de passe saisi par Claude.** Claude ne tape jamais un mot de passe. Les jetons de session se lisent depuis une session déjà ouverte par la personne et se rangent dans `~/.claude/secrets/`.

## Entretien dans le temps
- Tous les quelques mois, Claude regarde s'il existe un meilleur modèle local de la même taille et refait la mesure des 20 cas.
- Quand une ligne de commande casse, Claude note la date dans sa fiche, repasse sur le secours, et répare.

## Après
Coche la ligne `outils-locaux` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, puis propose la brique suivante : apps-locales-et-mods.
