---
name: veille-et-tendances
description: "Met en place la veille : tendances des 30 derniers jours, recherches que les gens tapent (insights de recherche TikTok, suggestions YouTube et Google), contenus hors norme des concurrents réécrits par l'angle. Utiliser quand l'utilisateur dit « qu'est-ce qui marche en ce moment », « surveille mes concurrents », « ce que les gens cherchent sur X ». Pas pour les questions de ses propres clients (utiliser banque-idees)."
---
# Veille et tendances

## Pourquoi
La banque d'idées dit ce que ses clients demandent. La veille dit ce que le marché regarde et cherche en ce moment. Dans le système d'origine, une veille quotidienne repérait les contenus qui faisaient plusieurs fois les vues habituelles de leur auteur, et une autre lisait les recherches auxquelles trop peu de vidéos répondent. Un essai de traduction mot à mot de posts viraux a fait monter les vues très vite, puis le comité d'experts l'a refusé : la plateforme repère le contenu non original et l'autorité du créateur s'abîme. La règle est restée : on garde l'angle et la forme, on réécrit tous les mots.

## Prérequis
- `banque-idees` (la veille y verse ses idées).
- Bloc C : le board des textes (`board-textes`), car tout texte réécrit passe la porte.
- Outils au choix, présentés comme options : un skill de recherche de tendances (type last30days), un compte TikTok pour Creator Search Insights, un outil comme vidIQ pour YouTube (payant), yt-dlp et une transcription locale (faster-whisper) si l'utilisateur accepte de les installer.

## Interview
Lis d'abord : la banque d'idées, la fiche client idéal, `wiki/maps/machine-contenu.md` (réseaux). Puis demande :
1. « Cite 5 à 15 comptes de ton domaine que tu admires ou qui te font concurrence. » Range dans `wiki/maps/veille.md`, section « Comptes suivis » (pseudo, réseau, langue).
2. « Quels mots tapent tes clients quand ils cherchent de l'aide ? » Range dans « Recherches à suivre ».
3. « Tu veux recevoir la veille quand ? » (chaque lundi, chaque jour, seulement en session). Range dans « Rythme ».
4. « Y a-t-il des thèmes à écarter d'office ? » (politique, religion, promos, mépris d'un groupe). Range dans « Filtres ».

## Construire
1. **Le score hors norme** (Claude, 15 min). Pour chaque compte suivi, le score d'un contenu = ses vues divisées par la médiane des vues du compte sur 30 jours. Ignore les contenus de moins de 48 h, qui montent encore, et les comptes de moins de 5 contenus sur la période. Un score de 5 ou plus mérite un regard. Écris ce calcul en script si l'utilisateur a un accès aux données (export, API, outil payant), sinon calcule sur ce qu'il colle. Ce score compare chaque créateur à lui-même, donc un petit compte qui explose remonte aussi.
2. **La réécriture par l'angle** (Claude, 15 min par idée). Pour un contenu retenu : transcris-le, écris en une ligne son angle (la situation, la tension, la promesse) et sa forme (durée, structure, type d'ouverture). Écris ensuite une version neuve pour le client idéal de l'utilisateur, avec ses mots à lui et une scène de sa vie. Aucune phrase de la source ne reste. Ne nomme jamais le créateur source dans le contenu.
3. **Les recherches** (Claude, 15 min). Tendances : lance le skill de tendances sur les mots de « Recherches à suivre ». YouTube et Google : relève les suggestions de saisie automatique (gratuites) et note les requêtes où le top 10 répond mal. TikTok : guide l'utilisateur dans l'application ou sur le web (recherche, puis « Creator Search Insights », onglet « Content gap ») pour sauvegarder les recherches mal servies. Chaque recherche retenue devient une ligne de la banque avec sa formulation exacte. Elle ira ensuite dans la phrase 1 ou 2, le texte à l'écran, le titre et la légende.
4. **Le rendez-vous** (Claude, 10 min). Une tâche planifiée (bloc F) prépare au rythme choisi les 3 meilleures idées, une seule par compte, dans `outputs/veille/AAAA-MM-JJ.md`. Un rendez-vous manqué (PC éteint) se rattrape au passage suivant. Pas de notification sauf demande.
5. **Le filtre** (Claude, 5 min). Chaque idée passe par les « Filtres » de l'interview avant d'entrer dans la banque. Le tri peut être un appel `claude -p` court par relevé (bloc B).

## Test
Le fichier de veille contient 3 idées, chacune avec son score, son angle en une ligne et une version réécrite qui ne partage aucune suite de plus de 5 mots avec la source.

## Pièges vécus
- Traduire tel quel ce qui marche ailleurs : des vues rapides, puis le risque d'être classé non original. Toujours passer par l'angle.
- Les recherches sortent souvent en anglais même avec un filtre de langue : traduis l'intention, jamais la phrase.
- Une version fidèle à une source qui parle à un autre public tombe à côté. Le mode libre a mieux noté devant le client idéal que le mode presque mot à mot.
- Certaines API refusent la recherche par mot-clé aux petites applications : garde toujours une voie manuelle.

## Entretien dans le temps
Après 4 semaines, règle le seuil du score selon ce que les idées retenues ont donné. Retire les comptes qui ne sortent jamais rien. Chaque idée publiée garde sa source de veille pour la mesure (`mesure-et-apprentissage`).

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (comptes et filtres choisis). Propose ensuite `sujet-en-pieces`.
