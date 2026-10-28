---
name: cockpit-app
description: "Installe le Cockpit, une app locale dans le navigateur qui dit en 5 secondes qui attend ta réponse, ta prochaine tâche, l'argent du mois, ta semaine, ton trimestre et les alertes ; un script construit state.json, un petit serveur local le sert, un raccourci bureau l'ouvre. Utiliser quand l'utilisateur dit « installe le cockpit », « ouvre le cockpit », « le cockpit est faux », « ajoute X au cockpit », « j'ai vendu ». Pas pour écrire le plan (utiliser plan-unique)."
---
# Cockpit (app locale)

## Pourquoi
Le fondateur du système d'origine avait des chiffres partout et ne regardait nulle part. Une première version du tableau de bord, dessinée dans l'interface de Claude Code, n'a jamais servi : elle était peu lisible, ses chiffres étaient faux et elle n'était pas à jour. La version qui a marché est une petite app locale avec un seul critère : en 5 secondes, il sait qui attend sa réponse, quelle est sa prochaine tâche et où en est l'argent du mois. Le script fait tous les calculs, la page ne fait que dessiner.

## Prérequis
- `plan-unique` (le plan au bon format) et `fiches-clients` (les fiches au bon format). Le Cockpit marche sans fiches ni ventes : il affiche « inconnu » ou « personne ».
- Python 3.8 ou plus récent, sans aucune bibliothèque à installer. Vérifie avec `python --version` (Windows) ou `python3 --version` (Mac, Linux).
- Outils joints dans `outils/` : `cockpit_build.py`, `cockpit_serveur.py`, `index.html`, `test_cockpit.py`, `lancer-cockpit.bat`, `lancer-cockpit.command`.

## Interview
**Lis d'abord** : `wiki/strategie/plan.md`, la liste des fiches dans `wiki/clients/`, `outputs/cockpit/` s'il existe, la règle des 4 % (pour savoir ce qui compte pour lui).

Puis demande :
1. Le matin, qu'est-ce que tu veux savoir avant tout le reste ? (Les blocs par défaut : attend ta réponse, prochaine tâche, argent du mois, semaine, trimestre, alertes.)
2. Un bloc te sert-il à rien ? Un manque-t-il ?
3. Tu veux un raccourci sur le bureau ?
4. Quel port te va ? (Par défaut 8787. Change seulement si un autre logiciel l'utilise.)

Range les réponses dans `wiki/maps/cockpit.md`.

## Construire
1. **Copier les outils (Claude, 5 min).** Copie le dossier `outils/` vers `scripts/cockpit/` du vault (sans `lancer-cockpit.*`, qui va à l'étape 5).
2. **Tester sur un faux vault (Claude, 5 min).** Lance `python -X utf8 scripts/cockpit/test_cockpit.py` (Mac, Linux : `python3`). Les tests créent un vault temporaire, construisent l'état, notent des ventes, démarrent le serveur sur un port libre et lisent la page. Tout doit finir par `OK`.
3. **Premier build réel (Claude, 5 min).** Depuis la racine du vault : `python -X utf8 scripts/cockpit/cockpit_build.py`. Lis la ligne affichée et les alertes de `outputs/cockpit/state.json`. Corrige le plan ou les fiches que l'alerte signale (« Fiche illisible », « Plan absent », « pas de ligne PROCHAINE »).
4. **Ouvrir l'app (utilisateur guidé, 2 min).** Lance `python -X utf8 scripts/cockpit/cockpit_serveur.py`. Le navigateur s'ouvre sur `http://127.0.0.1:8787/`. Demande à l'utilisateur de lire la page 5 secondes puis de dire, sans regarder, qui attend sa réponse et sa prochaine tâche.
5. **Raccourci bureau (Claude, 5 min).**
   - Windows : copie `outils/lancer-cockpit.bat` sur le Bureau sous le nom `Cockpit.bat`, remplace `CHEMIN_DU_VAULT` par le chemin du vault. Si le Bureau est synchronisé par un service de stockage en ligne, son vrai chemin peut être ailleurs que `C:\Users\<nom>\Desktop` : vérifie avec `[Environment]::GetFolderPath("Desktop")` dans PowerShell.
   - Mac : copie `outils/lancer-cockpit.command` sur le Bureau, remplace `CHEMIN_DU_VAULT`, puis `chmod +x ~/Desktop/lancer-cockpit.command`. Au premier double-clic, macOS peut demander l'autorisation dans Réglages, Confidentialité et sécurité : guide l'utilisateur.
   - Linux : même fichier, lancé depuis le gestionnaire de fichiers ou un lanceur `.desktop`.
   Si l'app tourne déjà, le raccourci ouvre simplement la page.
6. **Noter une vente (Claude, 1 min).** « J'ai vendu 1 500 à Alex » donne `python scripts/cockpit/cockpit_build.py vente 1500 "Alex"`. Chaque paiement reçu est une ligne de `outputs/cockpit/ventes.jsonl`, écrite en ajout seul.
7. **Ajouter un bloc (Claude, 20 min, seulement si demandé).** Toute donnée nouvelle se calcule dans `build_state` de `cockpit_build.py` et s'ajoute à `state.json`. `index.html` la dessine avec `textContent` (jamais `innerHTML` : une fiche ne doit jamais pouvoir injecter du code). Ajoute un test dans `test_cockpit.py` et relance l'étape 2.

**Contrat de `state.json`** (clés que les autres briques lisent) : `situation` (la ligne du début de conversation), `attente` (liste, plus ancien d'abord), `prochaine`, `argent` (`encaisse`, `cible`, `ventes`), `semaine`, `trimestre`, `cap`, `clients`, `alertes`.

## Test
`test_cockpit.py` sort `OK`, le raccourci bureau ouvre la page, et l'utilisateur dit juste, après 5 secondes de lecture, qui attend sa réponse et sa prochaine tâche.

## Pièges vécus
- **Le zéro qui ment.** Un compteur à 0 € quand la source était illisible faisait croire à un mois vide. Une donnée absente s'affiche « inconnu », jamais 0.
- **Le jargon à l'écran.** Des étiquettes internes (abréviations, noms de code) rendaient l'écran illisible pour son propre utilisateur. Écris tout en français simple, au tutoiement.
- **Deux builds en même temps.** Une tâche planifiée et un clic qui reconstruisent ensemble cassaient le fichier. Le serveur ne lance qu'un build à la fois, et l'écriture passe par un fichier temporaire remplacé d'un coup.
- **Des données clients qui sortent.** Le serveur écoute seulement sur 127.0.0.1 et ne sert que la page et `state.json`. Aucune donnée n'est envoyée à un service en ligne, et l'app n'appelle jamais Claude elle-même.
- **Une date passée présentée comme à venir.** Le plan disait « lundi » pour un lundi déjà passé. Le build lève une alerte pour chaque case datée d'avant aujourd'hui.

## Entretien dans le temps
- Le hook de début de conversation (voir `plan-unique`) lit `cockpit_build.py ligne` à chaque session.
- Avec le bloc F : une tâche planifiée relance le build chaque matin, et le rapport du matin reprend la ligne `situation`.
- Une fois par mois, demande à l'utilisateur quel bloc il ne lit jamais, et retire-le.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (« Cockpit : scripts/cockpit/, raccourci bureau, port 8787 »). Propose ensuite `crm-et-messages`.
