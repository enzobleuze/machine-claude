---
name: wrapper-de-tache
description: "Installe l'environnement commun (env.sh) et l'enveloppe run-tache.sh que toute tâche planifiée utilise : PATH sûr, journal daté, verrou anti-doublon, délai maximum, code de sortie, `claude -p` sur un modèle économique avec le jeton longue durée. Utiliser quand l'utilisateur dit « prépare le lanceur des tâches », « ma tâche marche à la main mais pas la nuit », « pourquoi elle a tourné deux fois ». Pas pour enregistrer l'horaire (utiliser taches-planifiees)."
---
# Wrapper de tâche

## Pourquoi
Une tâche planifiée démarre avec un PATH presque vide, sans tes variables, sans ton jeton. Dans le système d'origine, plusieurs tâches marchaient à la main et mouraient la nuit : un script avait oublié de charger l'environnement commun et une tâche hebdomadaire est restée morte deux semaines. Une autre fois, le jeton court de Claude expirait chaque nuit et tous les appels `claude -p` finissaient en 401. Depuis, chaque tâche passe par la même enveloppe, et aucune ne recode ces réglages.

## Prérequis
- Un vault avec `scripts/` et `outputs/` (bloc A).
- Windows : Git for Windows. Mac et Linux : bash.
- Pour les tâches qui appellent Claude : la brique « Claude sans fenêtre et jeton longue durée » du bloc B (jeton créé avec `claude setup-token`, rangé dans `~/.claude/secrets/claude-oauth-token.env`).

## Interview
Lis d'abord : `scripts/` (un `env.sh` existe peut-être déjà), `~/.claude/settings.json` (les plugins activés, sans afficher de secret), et `wiki/maps/automatisations.md`.
Puis demande :
1. « Tes tâches peuvent-elles appeler Claude, ou seulement des scripts ? » (si oui, on vérifie le jeton).
2. « Quel modèle pour les tâches ? Je conseille le modèle économique (Sonnet) pour tout, et le plus fort seulement pour une relecture qui compte. »
3. « Combien de temps maximum une tâche peut-elle tourner avant que je la coupe ? » (défaut 60 minutes).
Range les réponses dans `wiki/maps/automatisations.md` (section « Réglages ») et le choix du modèle en mémoire.

## Construire
1. **Copier (Claude, 2 min).** Copie `outils/env.sh`, `outils/run-tache.sh`, `outils/notify.sh` et `outils/notify.py` dans `<vault>/scripts/`. Ajoute à `.gitignore` : `outputs/cron-logs/.verrous/`.
2. **Vérifier l'environnement (Claude, 3 min).** Lance :
   `bash -c '. scripts/env.sh; echo PYTHON=$PYTHON; echo CLAUDE=${CLAUDE_BIN:+trouvé}; echo MODELE=$MODELE_TACHE; echo JETON=${CLAUDE_CODE_OAUTH_TOKEN:+présent}'`
   Il ne doit jamais afficher la valeur du jeton, seulement « présent ». Si `CLAUDE` est vide, règle `CLAUDE_BIN` en haut de `env.sh`.
3. **Créer le jeton si absent (l'utilisateur, 3 min).** Guide-le : ouvre un terminal normal (hors de Claude Code), tape `claude setup-token`, suis le lien, puis colle la ligne `CLAUDE_CODE_OAUTH_TOKEN=...` dans `~/.claude/secrets/claude-oauth-token.env`. Claude ne lit ni n'affiche ce fichier.
4. **Alléger le contexte des tâches (Claude, 5 min).** Crée `scripts/reglages-tache.json` qui coupe les plugins interactifs pour les tâches seulement : `{"enabledPlugins": {"<plugin>@<source>": false}}`, une ligne par plugin trouvé à l'étape 2 qui ne sert pas aux tâches. `claude_tache` l'utilise tout seul. Dans le système d'origine, ça a divisé le contexte de chaque appel par deux.
5. **Écrire une tâche selon la convention (Claude, 10 min).** Un script de tâche respecte ces codes de sortie : `0` fait, `2` l'humain doit agir, `3` arrêt propre qui reprendra (quota), tout autre code = panne. Exemple de tâche qui appelle Claude :
   ```bash
   #!/usr/bin/env bash
   # scripts/resume-semaine.sh : lancé par run-tache.sh
   . "$(dirname "$0")/env.sh"
   claude_tache "Lis wiki/journal/ des 7 derniers jours et écris outputs/semaine/$(date +%F).md" \
       --allowedTools "Read,Write,Glob,Grep" || exit 1
   [ -s "outputs/semaine/$(date +%F).md" ] || exit 1   # contrôle du fichier produit
   ```
6. **Essai à la main (Claude, 2 min).** `bash scripts/run-tache.sh essai echo bonjour`, puis lis `outputs/cron-logs/essai-<date>.log` et `outputs/cron-logs/.etat/essai.json`.

Ce que l'enveloppe fait seule : interrupteur général (`touch .machine-en-pause` à la racine arrête tout), verrou (un doublon sort sans rien faire, un verrou d'un processus mort est repris), journal daté, délai `TACHE_TIMEOUT_MIN`, état pour le gardien, notification selon le code.

## Test
`bash scripts/run-tache.sh essai bash -c 'exit 2'` écrit `"code": 2` dans `.etat/essai.json` et une ligne `[urgent]` dans `outputs/cron-logs/resume-<date>.log`. Lancé deux fois en même temps avec `sleep 5`, le second écrit « doublon ignoré ».

## Pièges vécus
- **Oublier de charger `env.sh`** : la tâche marche en session et meurt la nuit. Toute tâche passe par `run-tache.sh`, jamais par un appel direct.
- **401 la nuit** : le jeton court de l'app se rafraîchit pour l'app, pas pour `claude -p` lancé par une tâche. Redémarrer l'app ne répare rien. Seul le jeton longue durée règle ça. Si un 401 revient dans un an, régénère le jeton sans enquêter ailleurs.
- **Tâche « réussie » qui n'a rien produit** : un `claude -p` peut sortir 0 sans écrire le fichier. Termine chaque script par un contrôle du fichier attendu.
- **`%` dans un texte d'aide argparse** fait planter Python récent. Écris `%%`.
- **`localhost` lent sous Windows** : un appel à `localhost` peut perdre deux secondes par requête. Utilise `127.0.0.1` dans les scripts.
- **Crédit API ou abonnement** : si tu bascules les tâches sur une clé API, ajoute une sonde d'un jeton au début ; si l'API refuse, repasse sur l'abonnement tout seul au lieu de tout casser.

## Entretien dans le temps
Le gardien lit les états. Le rapport du matin compte les codes. L'âge du jeton longue durée se surveille : ajoute au gardien ou à une tâche mensuelle un contrôle « fichier du jeton plus vieux que 330 jours = warn ».

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Note le modèle choisi en mémoire. Propose ensuite taches-planifiees, puis notifications-telegram.
