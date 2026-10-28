---
name: notebooklm-brancher
description: "Branche NotebookLM à Claude Code par la commande notebooklm (paquet notebooklm-py) : installation, connexion, test, une question propre à un carnet avec garde-fou. Utiliser quand l'utilisateur dit « branche NotebookLM », « Claude peut interroger mes carnets ? », « NotebookLM ne répond plus ». Pas pour choisir ou remplir les carnets (utiliser carnets-experts)."
---
# Brancher NotebookLM à Claude

## Pourquoi
Un carnet NotebookLM répond seulement depuis les sources qu'on lui a données, avec la source citée. C'est le meilleur antidote aux conseils inventés : Claude demande à l'expert au lieu d'imaginer ce qu'il dirait, et ça coûte moins de jetons que relire les livres. Dans le système d'origine, un premier outil qui pilotait la page web s'est cassé au premier changement d'interface de Google. La commande `notebooklm` (paquet notebooklm-py, non officiel) parle directement au service et tient depuis des mois, à condition de suivre les garde-fous ci-dessous.

## Prérequis
- Un compte Google avec NotebookLM (l'offre gratuite suffit pour commencer ; ses limites de questions par jour et de sources par carnet sont plus basses que celles des offres payantes, voir la page d'aide Google).
- Python 3.10 ou plus récent, et `pip` (ou `uv`).
- Skill `architecture-vault` fait (bloc A) : les réponses se rangent dans `outputs/carnets/`.
- Coût : zéro en dehors de l'abonnement Google éventuel.
- À dire à l'utilisateur, en une phrase : l'outil est non officiel ; Google peut le casser ou le refuser un jour. On l'utilise avec son propre compte, sans rafales.

## Interview
Lis d'abord : `CLAUDE.md` du vault, la mémoire (une note `reference_notebooklm*` existe peut-être déjà), et lance `notebooklm --version` pour voir si l'outil est déjà là.

Puis demande, une question à la fois :
1. « Tu as déjà un compte NotebookLM ? Avec quelle adresse Google ? » (range l'adresse dans la note mémoire, jamais le mot de passe).
2. « Tu as l'offre gratuite ou payante ? » (range dans la note : elle fixe les limites).
3. « Tu utilises aussi NotebookLM à la main dans ton navigateur, sur les mêmes carnets ? » (si oui, prévenir du piège de `--new`, plus bas).
4. « Ton ordinateur reste allumé la journée, ou il dort souvent ? » (décide si une tâche de maintien de connexion vaut la peine).

Range tout dans `memory/reference_notebooklm.md` (adresse, offre, date du branchement, profil utilisé) et une ligne dans l'index MEMORY.

## Construire
1. **Installer l'outil** (Claude le fait).
   - Windows (PowerShell) : `python -m pip install --upgrade "notebooklm-py[browser]"`
   - Mac/Linux : `python3 -m pip install --upgrade "notebooklm-py[browser]"` (ou `uv tool install "notebooklm-py[browser]"`).
   - Vérifier : `notebooklm --version`. Si la commande est introuvable, ajouter le dossier `Scripts` (Windows) ou `~/.local/bin` (Mac/Linux) au PATH.
   - Si la connexion réclame un navigateur manquant : `python -m playwright install chromium`.
2. **Se connecter** (l'utilisateur le fait, Claude guide). Claude ouvre un terminal et lance `notebooklm login`. Dis à l'utilisateur : « Une fenêtre de navigateur s'ouvre. Connecte-toi à ton compte Google comme d'habitude, jusqu'à voir la page d'accueil de NotebookLM. Puis reviens dans le terminal et fais ce qu'il demande (souvent : appuyer sur Entrée). » Claude ne voit et ne tape jamais le mot de passe.
3. **Tester la connexion** (Claude) : `notebooklm auth check --test --json` doit dire `"status": "ok"`. Puis `notebooklm list` : la liste des carnets s'affiche avec leurs identifiants.
4. **Poser le garde-fou** (Claude). Copie `outils/nlm_ask.py` dans `scripts/nlm_ask.py` du vault, puis `python scripts/nlm_ask.py selftest` doit imprimer `selftest OK`. À partir de là, toute question passe par :
   ```
   python scripts/nlm_ask.py ask <carnet> <question.txt> --sortie outputs/carnets/<date>-<sujet>
   ```
   Le script lance `notebooklm ask -n <id> --new --yes --json --prompt-file <question.txt>`, puis vérifie la réponse (voir Pièges). Sorties : 0 acceptée, 1 refusée par le garde-fou, 2 panne, 4 question trop longue. `<carnet>` peut être une clé du registre `carnets.json` (skill `carnets-experts`).
5. **Écrire la règle d'usage** dans `CLAUDE.md` du vault (Claude), en quatre lignes :
   - Toujours `scripts/nlm_ask.py` ou, à la main, `notebooklm ask -n <id> --new --yes --prompt-file <f>`. Jamais `notebooklm use` seul.
   - Question dans un fichier, moins de 3 800 signes, première ligne : « Réponds UNIQUEMENT depuis les sources de ce carnet et cite la source de chaque point ; si tes sources ne disent rien sur un point, écris AUCUNE SOURCE. »
   - Une réponse refusée par le garde-fou ne sert jamais.
   - La réponse est de la matière première : on la reformule dans la voix de l'utilisateur, on ne la colle pas.
6. **Maintien de connexion** (facultatif, si l'ordinateur reste allumé). Les cookies de session expirent vite. Une tâche qui lance `notebooklm auth refresh --quiet` toutes les 20 minutes aide.
   - Windows : `schtasks /Create /SC MINUTE /MO 20 /TN "NotebookLM refresh" /TR "cmd /c notebooklm auth refresh --quiet"`
   - Mac/Linux : `crontab -e` puis `*/20 * * * * notebooklm auth refresh --quiet`
   Demande l'accord avant de créer la tâche (c'est une configuration permanente).

## Test
`python scripts/nlm_ask.py auth` sort 0, puis une vraie question sur un carnet de l'utilisateur sort 0 avec un fichier `.answer.md` qui cite au moins une source. Les deux, sinon ce n'est pas branché.

## Pièges vécus
- **`notebooklm use` ne suffit pas.** `ask` continue la DERNIÈRE conversation ouverte, parfois sur un autre carnet. Symptôme vécu : on interroge l'expert vente et la réponse sort du carnet relationnel. Remède : carnet explicite (`-n`) et conversation neuve (`--new`) à chaque question.
- **`--new` efface la conversation en cours sur ce carnet**, côté serveur. Si l'utilisateur discute aussi à la main avec ce carnet dans son navigateur, il perd ce fil. Lui dire, ou lui créer un carnet à lui.
- **Taille.** Au-delà d'environ 4 000 signes, NotebookLM refuse la question (« Chat request was rejected by the server (status 3) »). Le script bloque au-dessus de 3 800 et demande de découper en lots de 4 à 6 points.
- **« The sources do not contain... »** veut souvent dire que la question était trop large, même sur le bon carnet. Resserrer la question et relancer une fois.
- **Sans la phrase d'amorce**, un carnet est revenu sans aucune source citée. Le garde-fou refuse alors la réponse : c'est voulu.
- **Accents cassés sous Windows** : le script force `PYTHONUTF8=1`. À la main, le mettre aussi.
- **Connexion qui meurt au bout d'une heure environ.** Google a révoqué à plusieurs reprises les sessions créées par le navigateur de l'outil. Ce qui a tenu : se connecter dans un vrai navigateur du quotidien, puis importer ses cookies (`notebooklm login --browser-cookies firefox`, ou le nom de son navigateur ; vérifier avec `notebooklm login --help`), avec la tâche de maintien. Le navigateur a mieux tenu quand il n'était pas de la famille Chrome. Et l'utilisateur ne se déconnecte jamais de Google dans ce navigateur. Un antivirus a supprimé le lecteur de cookies à l'installation : si l'import dit « not installed », regarder la quarantaine de l'antivirus.
- **Ne crée pas de compte Google « jetable » pour l'outil.** Un compte neuf dédié au robot a été suspendu par Google pour activité automatisée. On reste sur le vrai compte, à un rythme humain : une question à la fois, une pause entre deux.
- **Changement d'adresse côté Google.** Un jour tout a cassé (« CSRF token not found »). Remède : mettre l'outil à jour (étape 1), renommer le dossier du profil navigateur de l'outil (`notebooklm doctor` donne son chemin), se reconnecter.
- **Le plafond de questions par jour dépend de l'offre.** Ne bride pas par prudence : on s'arrête sur un vrai refus de NotebookLM, jamais avant.

## Entretien dans le temps
- Chaque début de séance qui va interroger les carnets : `python scripts/nlm_ask.py auth`. Sortie 2 : l'utilisateur relance `notebooklm login`, rien d'autre ne dépend de lui.
- Une fois par mois : `python -m pip install --upgrade "notebooklm-py[browser]"`, puis le selftest et une question test.
- Toute panne nouvelle et son remède vont dans `memory/reference_notebooklm.md`.

## Après
Mets à jour `wiki/maps/parcours.md` (brique faite, date), ajoute une entrée à `log.md`, complète la note mémoire. Propose ensuite `carnets-experts`.
