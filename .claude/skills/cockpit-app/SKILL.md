---
name: cockpit-app
description: "Installe le Cockpit, une app locale aux couleurs de la marque, ouverte d'un raccourci sur le bureau : Aujourd'hui (qui attend ta réponse, prochaine tâche, argent du mois, semaine, alertes, agenda), Clients (dossier complet, notes, prochaine étape, écran d'appel), Échelle d'offres, Agenda et rythme, Réseaux, Tournage et Plan avec le parking à idées. Chaque source se branche à part et l'écran dit quoi brancher tant qu'elle manque. Utiliser quand l'utilisateur dit « installe le cockpit », « ouvre le cockpit », « le cockpit est faux », « ajoute X au cockpit », « branche mon agenda au cockpit », « j'ai vendu ». Pas pour écrire le plan (utiliser plan-unique) ni pour une petite app d'un autre sujet (utiliser apps-locales-et-mods)."
---
# Cockpit (app locale)

## Pourquoi
Le fondateur du système d'origine avait des chiffres partout et ne regardait nulle part. Une première version du tableau de bord, dessinée dans l'interface de Claude Code, n'a jamais servi : peu lisible, chiffres faux, jamais à jour. La version qui a tenu est une app locale dans le navigateur avec un seul critère : en 5 secondes, il sait qui attend sa réponse, quelle est sa prochaine tâche et où en est l'argent du mois. Elle a ensuite grandi pour suivre des dizaines de clients sans se perdre, avec le dossier complet de chaque personne sous les yeux et dans un fichier que Claude lit avant d'écrire. Le moteur fait tous les calculs, la page ne fait que dessiner, et rien ne part vers une personne depuis l'app.

## Prérequis
- `plan-unique` (le plan au bon format) et `fiches-clients` (les fiches au bon format). Le Cockpit s'ouvre sans eux : chaque bloc vide dit en une phrase quoi faire.
- `charte-graphique` conseillé : sans charte, le Cockpit prend la charte « simple » et le dit une fois à l'écran.
- Sources facultatives, branchées une à une plus tard : `taches-source-unique` (Linear ou un fichier), un agenda Google ou Outlook, `offre-et-echelle`, `mesure-et-apprentissage`, `script-video` et `reels-et-shorts`, `appel-de-vente`, et le bloc F pour les alertes du système.
- Python 3.8 ou plus récent, sans bibliothèque à installer. Vérifie avec `python --version` (Windows) ou `python3 --version` (Mac, Linux). Aucun coût.
- Outils joints dans `outils/` : `cockpit_build.py` (le moteur), `cockpit_sources.py` (les sources branchables), `cockpit_serveur.py` (le serveur local), `index.html` (la page), `charte-simple.css` (la charte de secours), `cockpit_demo.py` (un faux vault pour la démo et les tests), `test_cockpit.py`, `lancer-cockpit.bat` et `lancer-cockpit.command`.

## Interview
**Lis d'abord** : `wiki/strategie/plan.md`, la liste des fiches de `wiki/clients/`, `wiki/business/echelle-offres.md`, `wiki/maps/taches.md` ou les connecteurs branchés (`claude mcp list`), les noms des fichiers de `~/.claude/secrets/` (jamais leur contenu), `bibliotheque/marque/charte-jetons.json`, `wiki/maps/regle-4-pourcent.md`, `wiki/scripts/script-appel.md`, et `scripts/cockpit/reglages.json` s'il existe déjà.

Puis demande, une question à la fois :
1. « Le matin, qu'est-ce que tu veux savoir avant tout le reste ? » Par défaut : qui attend ta réponse, ta prochaine tâche, l'argent du mois.
2. « Parmi ces écrans, lesquels te serviront ? Aujourd'hui, Clients, Échelle, Agenda, Réseaux, Tournage, Plan. » Ceux qu'elle ne veut pas sortent de la barre (réglage `ecrans`) ; Aujourd'hui reste toujours.
3. « Où vivent tes tâches : Linear, un simple fichier, ou nulle part pour l'instant ? »
4. « Ton agenda est sur Google, sur Outlook, ou ailleurs ? »
5. « Quels réseaux veux-tu suivre ? »
6. « Quelles commandes tapes-tu souvent dans Claude ? » Elles deviennent des boutons qui se copient en haut de la page (par défaut `/reprise`, `/passation`, `/cerveau`, `/fin`).
7. « Au bout de combien de jours une personne qui attend ta réponse doit devenir une alerte ? » (par défaut 2) « Combien de grands chantiers en même temps, au plus ? » (par défaut 2)
8. « Tu veux un raccourci sur le bureau ? » Le port par défaut est 8787 ; change-le seulement si un autre logiciel l'utilise.

Range les réponses dans `wiki/maps/cockpit.md` (avec 3 liens : plan, parcours, routage) et les réglages dans `scripts/cockpit/reglages.json` (étape 4).

## Construire
1. **Copier les outils (Claude, 5 min).** Copie le dossier `outils/` vers `scripts/cockpit/` du vault, sans `lancer-cockpit.*` (étape 8). Ajoute au `.gitignore` du vault les fichiers que le moteur recalcule : `outputs/cockpit/state.json`, `outputs/cockpit/cache/`, `outputs/cockpit/dossiers/`, `outputs/cockpit/.build.lock`. Les ventes, les notes et les décisions restent suivies, dans le dépôt privé, comme les fiches.
2. **Tester sur le faux vault (Claude, 5 min).** `python -X utf8 scripts/cockpit/test_cockpit.py` (Mac, Linux : `python3`) puis `python -X utf8 scripts/cockpit/cockpit_build.py --check`. Les tests créent un vault inventé, simulent Linear sans réseau, lisent un agenda local, démarrent le serveur sur un port libre et vérifient chaque écriture. Tout doit finir par `OK` et `contrôles OK`.
3. **Montrer la démo (utilisateur guidé, 5 min).** `python -X utf8 scripts/cockpit/cockpit_serveur.py --demo`. Le navigateur s'ouvre sur un faux vault aux noms inventés, dans un dossier temporaire : rien ne touche ses vraies données. Fais-lui parcourir les écrans avec les touches 1 à 7, puis `?` pour l'aide. Dis-lui : « Chaque bouton « Copier pour Claude » met une consigne prête dans ton presse-papiers. Tu la colles dans une conversation. L'app n'envoie jamais rien à personne. » Arrête la démo (Ctrl+C dans le terminal).
4. **Les réglages (Claude, 5 min).** Écris `scripts/cockpit/reglages.json` avec les réponses de l'interview. Une clé absente garde sa valeur par défaut :
   ```json
   {"port": 8787, "attenteJours": 2, "chantiersMax": 2, "motsParMinute": null,
    "commandes": ["/reprise", "/passation", "/cerveau", "/fin"],
    "reseaux": ["instagram", "youtube"],
    "ecrans": ["today", "clients", "echelle", "agenda", "reseaux", "tournage", "plan"],
    "linearEquipe": null}
   ```
   `motsParMinute` reste `null` tant que son rythme de parole n'est pas mesuré : l'écran Tournage n'affiche alors que le nombre de mots, jamais une durée devinée. `linearEquipe` sert seulement si son espace Linear a plusieurs équipes (sinon la première est prise).
5. **Premier build réel (Claude, 10 min).** Depuis la racine du vault : `python -X utf8 scripts/cockpit/cockpit_build.py`. Lis la ligne affichée et les alertes de `outputs/cockpit/state.json`. Corrige le plan ou les fiches que l'alerte signale (« Fiche illisible », « Plan absent », « pas de ligne PROCHAINE »).
6. **Brancher les sources, une à la fois (20 min chacune, seulement celles qu'elle veut).** Chaque source manquante laisse son bloc vide avec la phrase qui dit quoi brancher, et le reste du Cockpit marche.

   | Source | Ce que le Cockpit lit | Ce que fait l'utilisateur | Ce que fait Claude |
   |-|-|-|-|
   | Tâches Linear | `~/.claude/secrets/linear.env` : `LINEAR_API_KEY=...` (clé personnelle) | Crée la clé dans Linear (réglages du compte, « Security & access », « Personal API keys ») et la colle dans le fichier ouvert par Claude | Ouvre le fichier pour elle (Windows : `notepad %USERPROFILE%\.claude\secrets\linear.env` ; Mac : `open -e ~/.claude/secrets/linear.env`), relance le build, vérifie que « Chantiers » affiche Linear |
   | Tâches sans Linear | `wiki/maps/taches.md` : sections « En cours », « À faire », une case par tâche, échéance `AAAA-MM-JJ` dans le texte | Rien | Crée le fichier (skill `taches-source-unique`) |
   | Agenda | `~/.claude/secrets/agenda.env` : `AGENDA_ICAL_URL=...` (un deuxième agenda : `AGENDA_ICAL_URL_2=...`) | Copie l'adresse secrète iCal. Google Agenda : Paramètres, puis son agenda, puis « Intégrer l'agenda », puis « Adresse secrète au format iCal ». Outlook : Paramètres, Calendrier, Calendriers partagés, « Publier un calendrier », lien ICS | Ouvre le fichier comme pour Linear, relance, vérifie l'écran Agenda. L'adresse ne passe jamais dans la conversation |
   | Échelle | `wiki/business/echelle-offres.md` : le premier tableau (colonnes Marche, Prix, Ce qu'elle contient, Marche suivante, Où on la montre, et une colonne facultative « Quand la proposer ») | Dit quand proposer chaque marche | Ajoute la colonne « Quand la proposer » ; sans elle, l'écran dit « règle à écrire » au lieu d'inventer un moment |
   | Réseaux | `outputs/cockpit/reseaux/releves.jsonl` (`{"date", "reseau", "abonnes", "source"}`), `publications.jsonl` (`date, reseau, titre, url, vues`), `commentaires.jsonl` (`id, reseau, auteur, texte, date, publication, url`) | Note ses abonnés à la main dans l'écran, ou dit « relève mes réseaux » | Remplit les trois fichiers depuis le navigateur ou une API (skill `mesure-et-apprentissage`), puis une tâche planifiée le fait chaque semaine (bloc F) |
   | Tournage | `outputs/youtube/<slug>/script.md` avec `board.md` à côté, `outputs/courts/scripts/<n>-<slug>.md` avec `<n>-<slug>.board.md` | Rien | Écrit le verdict du board en ligne `## Verdict : VERT` ; la copie pour le prompteur est refusée sans VERT, et refusée si la porte du board (`scripts/porte_board.py`) dit que le texte a changé |
   | Appel | `wiki/scripts/script-appel.md` : un titre `##` par phase, un paragraphe qui commence par `>` est dit à voix haute, les autres sont des consignes, `[prénom]` est remplacé, une section `## Sécurité` devient un bandeau fixe ; `wiki/scripts/objections-reponses.md` : un titre par objection | Répète sur `#appel/essai` (rien n'est écrit) | Met le script au format (skill `appel-de-vente`) |
   | Alertes du système | `outputs/cron-logs/resume-<date>.log` écrits par `notify` (bloc F) | Rien | Rien : une ligne `[ok]` plus récente règle l'alerte du même titre |
   | Charte | `bibliotheque/marque/charte.css` et `charte-jetons.json` (nom, logo, thème principal) | Choisit sa charte (skill `charte-graphique`) | Rien de plus : le Cockpit suit au prochain rechargement |
7. **Ouvrir l'app (utilisateur guidé, 2 min).** `python -X utf8 scripts/cockpit/cockpit_serveur.py`. Le navigateur s'ouvre sur `http://127.0.0.1:8787/`. Demande-lui de lire la page 5 secondes, puis de dire sans regarder qui attend sa réponse et sa prochaine tâche.
8. **Raccourci bureau (Claude, 5 min).**
   - Windows : copie `outils/lancer-cockpit.bat` sur le Bureau sous le nom `Cockpit.bat`, remplace `CHEMIN_DU_VAULT` par le chemin du vault. Si le Bureau est synchronisé par un service de stockage en ligne, son vrai chemin peut être ailleurs que `C:\Users\<nom>\Desktop` : vérifie avec `[Environment]::GetFolderPath("Desktop")` dans PowerShell.
   - Mac : copie `outils/lancer-cockpit.command` sur le Bureau, remplace `CHEMIN_DU_VAULT`, puis `chmod +x ~/Desktop/lancer-cockpit.command`. Au premier double-clic, macOS peut demander l'autorisation dans Réglages, Confidentialité et sécurité : guide-la.
   - Linux : même fichier, lancé depuis le gestionnaire de fichiers ou un lanceur `.desktop`.
   Si l'app tourne déjà, le raccourci ouvre simplement la page.
9. **Noter une vente (Claude, 1 min).** « J'ai vendu 1 500 à Alex pour l'accompagnement » donne `python scripts/cockpit/cockpit_build.py vente 1500 "Alex" --offre "Accompagnement"`. Dans la page : touche `V` sur Aujourd'hui, ou « Vendu » en fin d'appel. Chaque paiement reçu est une ligne de `outputs/cockpit/ventes.jsonl`, écrite en ajout seul. L'offre nommée fait monter la personne sur l'échelle.
10. **Le dossier pour Claude (Claude, 5 min).** Le bouton « Copier pour Claude : dossier complet » d'une fiche (ou `cockpit_build.py dossier <id>`) écrit `outputs/cockpit/dossiers/<id>.md` : où on en est, contrat, échelle, notes, derniers échanges encadrés comme texte d'un tiers. Ajoute au `CLAUDE.md` : « Avant de préparer une réponse à un client, lis son dossier `outputs/cockpit/dossiers/<id>.md` s'il existe, puis sa fiche. »
11. **Le build du matin (Claude, 5 min, si le bloc F est installé).** Une tâche planifiée lance `python -X utf8 scripts/cockpit/cockpit_build.py` chaque matin avant le rapport du matin. Quand le serveur tourne, il refait aussi le build toutes les 15 minutes.
12. **Ajouter un bloc ou un écran (Claude, 20 min, seulement si elle le demande).** Toute donnée nouvelle se calcule dans `build_state` de `cockpit_build.py`, ou dans une source de `cockpit_sources.py` qui rend `etat` et `consigne`. La page la dessine dans `index.html` : tout texte passe par `esc()`, `put()` reste la seule affectation de HTML, et les couleurs viennent seulement des variables de la charte (`--fond`, `--surface`, `--accent`...). Toute écriture passe par une route POST du serveur qui valide ses entrées et n'accepte qu'un identifiant que l'état connaît. Ajoute un test dans `test_cockpit.py`, relance l'étape 2, puis regarde le résultat avec `--demo`.

**Ce que la page écrit, et rien d'autre** : `outputs/cockpit/` (ventes, décisions, notes, commentaires d'agenda, relevés et commentaires traités, fiches d'appel, dossiers), la section « À trier » de `wiki/maps/parking.md`, l'état de tournage à côté des scripts, et les tâches Linear quand elle clique (marquer faite et retirer demandent un deuxième clic). Aucun message envoyé, aucune publication, aucun appel à Claude depuis l'app. Le serveur écoute seulement sur 127.0.0.1 : la page ne s'ouvre pas depuis un autre appareil.

**Contrat de `state.json`** (clés que les autres briques lisent, à ne pas renommer) : `situation`, `attente`, `prochaine`, `argent` (`encaisse`, `cible`, `ventes`), `semaine`, `trimestre`, `cap`, `clients`, `alertes` (une phrase par alerte à régler). Clés de la page : `personnes`, `plan`, `entonnoir`, `alertesDetail`, `taches`, `agenda`, `rythme`, `echelle`, `reseaux`, `tournage`, `appel`, `idees`, `charte`, `reglages`.

## Test
Les quatre sont vrais :
- `test_cockpit.py` sort `OK` et `cockpit_build.py --check` sort `contrôles OK`.
- Le build réel ne signale aucune « Fiche illisible », et chaque bloc sans source affiche sa phrase « branche ceci » au lieu d'un faux zéro.
- Le raccourci bureau ouvre la page aux couleurs de sa charte (ou la charte simple, annoncée une fois).
- Après 5 secondes de lecture, l'utilisateur dit juste qui attend sa réponse et sa prochaine tâche.

## Pièges vécus
- **Le zéro qui ment.** Un compteur à 0 € quand la source était illisible faisait croire à un mois vide. Une donnée absente s'affiche « inconnu » ou « à remplir », jamais 0, et un vrai zéro s'imprime.
- **Le jargon à l'écran.** Des étiquettes internes (abréviations, noms de code) rendaient l'écran illisible pour son propre utilisateur. Tout est écrit en français simple, au tutoiement, une idée par phrase.
- **La fiche « actif » jamais mise à jour.** Des fiches importées d'un ancien outil disaient « actif » pour des clients partis depuis longtemps. Une fiche active sans échange depuis 3 mois passe en ancien client, avec la phrase qui le dit, et un bouton permet de la remettre en actif.
- **Le paiement contradictoire.** Deux sources disaient l'une « payé en entier », l'autre « paiement partiel », et l'écran affichait un faux impayé. Le reste à payer se calcule seulement quand les deux chiffres sont connus ; sinon il s'écrit « à vérifier ».
- **Une date passée présentée comme à venir.** Le plan disait « lundi » pour un lundi déjà passé. Chaque case datée d'avant aujourd'hui lève une alerte.
- **Un agent de test qui clique dans les vraies données.** Un test automatique a archivé plusieurs vrais clients en cliquant dans l'app réelle. Les tests et les essais tournent sur le faux vault (`--demo`, `test_cockpit.py`), jamais sur l'app réelle.
- **Deux builds en même temps.** Une tâche planifiée et un clic qui reconstruisaient ensemble cassaient le fichier. Un verrou laisse passer un seul build, l'écriture passe par un fichier temporaire remplacé d'un coup, et un service de synchronisation qui tient le fichier une seconde a droit à quelques essais. Un fichier de décisions abîmé est copié à côté avant d'être réécrit.
- **Le texte d'un tiers qui donne des ordres.** Un message de client collé tel quel dans une consigne pour Claude peut contenir des instructions. Dans chaque « Copier pour Claude » et dans le dossier, il est encadré comme une donnée, et le texte ne peut pas refermer son cadre (les crochets et les mots du cadre en sont retirés).
- **L'adresse de l'agenda dans un message.** L'adresse iCal secrète donne accès à tout l'agenda. Elle vit dans `~/.claude/secrets/`, et ni l'état, ni un journal, ni un message d'erreur ne la reprend.
- **La prévision inventée.** Une courbe tracée sur deux points promettait une date au hasard. Le rythme dit « inconnu » tant qu'il n'y a pas 3 relevés et qu'aucune avancée n'est mesurée, et chaque prévision dit sa méthode.
- **Le prompteur sur un texte non validé.** Un script modifié après le verdict du board aurait pu être tourné. La copie pour le prompteur exige VERT, et la porte du board quand elle est installée.
- **Une page ouverte depuis un autre site.** Une revue de sécurité a montré qu'un site piégé pouvait viser un serveur local. Le serveur refuse tout en-tête Host étranger, toute écriture sans Origin de la page, tout envoi de plus de 64 Ko.

## Entretien dans le temps
- Le hook de début de conversation (voir `plan-unique`) lit `cockpit_build.py ligne` à chaque session. Cette commande ne touche jamais le réseau : elle prend la dernière copie de Linear et de l'agenda. Elle a besoin de `cockpit_sources.py` à côté d'elle.
- Le build tourne chaque matin (bloc F) et toutes les 15 minutes quand la page est ouverte. Un relevé de réseau de plus de 7 jours devient une info « relève mes réseaux ».
- Une fois par mois, demande à l'utilisateur quel écran ou quel bloc il ne lit jamais, et retire-le (réglage `ecrans`, ou le bloc dans `index.html`).
- Après une mise à jour du kit, recopie `outils/` (en gardant `reglages.json`), relance `test_cockpit.py`, puis ouvre la page.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md` et la mémoire (« Cockpit : scripts/cockpit/, raccourci bureau, port, sources branchées »). Ajoute à `wiki/maps/routage.md` : « ouvre le cockpit », « branche mon agenda au cockpit », « branche Linear au cockpit », « relève mes réseaux », « dossier complet de X », « mode démo du cockpit ». Propose ensuite `crm-et-messages`.
