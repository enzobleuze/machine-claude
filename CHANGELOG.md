# Changelog

Chaque version est datée. Pour mettre à jour une installation : « Mets à jour la machine depuis ce dossier » (voir INSTALLER.md, dernière section).

## 2026-10-29 : version 1.3.1 (correctif de sécurité, s'applique après la version 1.3)
- `cockpit-app` : dans les messages que le Cockpit prépare pour Claude, le texte venu de tiers est désormais encadré comme une donnée à ne pas exécuter : titres d'invitations d'agenda et de tâches, comptes rendus d'appels, coordonnées, raisons de refus. Une invitation piégée ne peut plus glisser une consigne à Claude. Les notes écrites par l'utilisateur restent telles quelles. Un test vérifie l'encadrement.
- Pour une installation existante : « Mets à jour le Cockpit depuis ce dossier » (Claude recopie `cockpit_build.py`, `index.html` et `test_cockpit.py`, puis relance les tests).

## 2026-10-29 : version 1.3 (s'applique après la version 1.2)
- Nouvelle brique `charte-graphique` (bloc D, avant le Cockpit) : couleurs, polices, logo et ambiance dans `bibliotheque/marque/charte.json`. Reprend une identité existante, ou propose quatre chartes prêtes plus une sur mesure sur une page d'aperçu, ou part d'une charte simple. `charte.py` déduit le reste (surfaces, thème clair et sombre, couleurs d'état), garantit les contrastes et écrit `charte.css` et `charte-jetons.json`, que lisent tous les outils visuels.
- `cockpit-app` au niveau du système d'origine : écrans Aujourd'hui, Clients (dossier complet pour Claude), Appel (avec répétition), Échelle, Agenda (iCal, Linear), Réseaux, Tournage, Plan ; ventes, ligne de situation, recherche rapide, aide, mode démo, clair et sombre aux couleurs de la charte. Nouveaux : `cockpit_sources.py`, `cockpit_demo.py`, `charte-simple.css`. 31 tests hors ligne.
- Carrousels : `carrousel-html` passe à 5 styles plus conversation et pub statique, avec contrôles (débordement, zone sûre, contraste), carrousels tirés d'un Reel ou d'une vidéo longue, page de revue et file du jour (`file.py`), option mode photo TikTok (`tiktok-photo.py`). `carrousel-image-ia` reçoit `carrousel-ia.py` (règles, prompts tirés de la charte, banque, finition).
- Vidéo : `montage-video-code` reçoit une chaîne complète (transcription, coupes des silences, « euh » et bruits de bouche, habillage, chapitres, B-roll, contrôle du rythme, page de revue, rendu sur carte graphique ou processeur). `reels-et-shorts` reçoit les gabarits rythme, éditorial et simple ; `sons-et-musique` la sonothèque et le mixage ; `tournage` la garde de prise ; `decoupe-shorts` le mode buste. Tout l'habillage suit la charte.
- `/vente` note aussi la vente pour le Cockpit ; `plan-unique` copie `cockpit_sources.py` avec le moteur.
- Pour une installation existante : « Mets à jour la machine depuis ce dossier », puis « Pose ma charte graphique ». Ensuite, selon ce qui est déjà installé : « Mets à jour le Cockpit », « Mets à jour mes carrousels », « Mets à jour mon montage vidéo » (Claude recopie les nouveaux outils et relance leurs tests).

## 2026-10-28 : version 1.2 (s'applique après la version 1.1)
- `notebooklm-brancher` : la connexion qui tient. Google coupait en une heure environ les connexions ouvertes par le navigateur de l'outil. Nouvelle marche par défaut sous Windows : `outils/reparer-connexion.ps1`, lancé par l'utilisateur dans un terminal administrateur, hors de l'application Claude (Firefox, exclusion antivirus du seul lecteur de cookies, import de la connexion, vérification) ; il pose la tâche « NotebookLM garder connexion » qui lance `outils/garder-connexion.pyw` toutes les 20 minutes et écrit `~/.notebooklm/ALERTE-connexion.txt` après 3 échecs de suite. Quatre pièges vécus en plus.
- `taches-source-unique` : Linear branché par clé personnelle (n'expire pas, ne passe jamais dans la conversation), visite guidée `outils/expliquer-linear.md` pour que Claude explique l'outil et fasse pratiquer, un test de plus.
- Pour une installation existante : « Mets à jour la machine depuis ce dossier », puis « Répare la connexion NotebookLM » (si NotebookLM est déjà branché) et « Branche Linear ». Les deux lignes de routage s'ajoutent à `wiki/maps/routage.md`.

## 2026-10-28 : version 1.1 (s'applique après la version 1 du même jour)
- Nouvelle brique `dossier-client-ideal` (bloc D, juste après `entretien-fondateur`) : le client idéal mot à mot et sourcé en 12 parties (douleurs, peurs, désirs classés, rêves, déjà essayé, mythes, fausses solutions, ce qu'il ne veut plus être, objections, déclic, mots exacts, mots à bannir), la précision émotionnelle en 3 niveaux avec sa bibliothèque de micro-moments, et un fichier de pensées par situation. Gabarits, exemple rempli, questions pour les carnets et `verifier-dossier.py` (`--test`) dans `.claude/skills/dossier-client-ideal/outils/`.
- Pour une installation existante : copie le skill, copie `verifier-dossier.py` dans `scripts/` du vault, ajoute la section « Écrire pour son client » de `CLAUDE.modele.md` au `CLAUDE.md`, la ligne `dossier-client-ideal` dans `wiki/maps/routage.md`, et la brique dans `wiki/maps/parcours.md` (bloc D, après `entretien-fondateur`, état selon ce qui existe déjà dans `wiki/business/`).
- `GUIDE-CONTENU.md` : le chemin pas à pas pour l'humain, du premier entretien au contenu publié et mesuré (NotebookLM et carnets compris).
- Bloc E : chaque skill de contenu lit d'abord le dossier du client idéal ; accroche, vidéo courte et email s'ouvrent sur un niveau 3.

## 2026-10-28 : version 1
- Première version : installateur, cœur CLAUDE.md, blueprint en 6 blocs (cerveau, méthode, experts, business, contenu, automatisation).
- 84 skills : une recette par brique, chacune avec interview, construction pas à pas, test et pièges vécus.
- Outils testés : hooks de sécurité, bibliothécaire, recherche par le sens, porte du board, lint de voix, contrôle de vérité, Cockpit, carrousels, essais, découpe de Shorts, tâches planifiées, gardien, notifications, rapport du matin.
- Commandes : /reprise, /passation, /fin, /cerveau, /idee, /vente, /ingest, /lint.
- Contrôle unique : `python scripts/verifier-installation.py` (PASS ou ÉCHEC).
