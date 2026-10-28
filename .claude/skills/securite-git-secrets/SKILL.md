---
name: securite-git-secrets
description: "Met le vault en sécurité : dépôt git local, dépôt GitHub PRIVÉ poussé plusieurs fois par jour, secrets rangés hors du vault avec un garde-fou qui refuse de les pousser, hook qui bloque les commandes destructrices. Utiliser quand l'utilisateur dit « j'ai peur de tout perdre », « sauvegarde sur GitHub », « où je mets mes clés », « brique ». Pas pour les copies Drive et le coffre chiffré (utiliser sauvegardes-3-lieux)."
---
# Sécurité : git, GitHub privé, secrets, anti-suppression

## Pourquoi
Dans le système d'origine, trois peurs revenaient : perdre une journée de travail, voir une clé d'API fuiter, et laisser Claude détruire un dossier par une commande trop rapide. Git avec un dépôt GitHub privé poussé plusieurs fois par jour a réglé la première : chaque version du texte est récupérable. Les secrets rangés dans `~/.claude/secrets/`, jamais dans le vault, ont réglé la deuxième, car l'historique git garde tout pour toujours. Le hook anti-suppression a réglé la troisième en bloquant `rm -rf`, `git reset --hard` et leurs cousins.

## Prérequis
- architecture-vault fait.
- Git. Windows : `winget install Git.Git` (donne aussi Git Bash). Mac : `xcode-select --install` ou `brew install git`.
- Un compte GitHub (gratuit, dépôts privés illimités) et GitHub CLI : Windows `winget install GitHub.cli`, Mac `brew install gh`.
- Node.js pour le hook (déjà installé par bibliothecaire-installer, sinon `winget install OpenJS.NodeJS.LTS` ou `brew install node`).
- Fichiers du socle : `.claude/hooks/anti-suppression.js` et `.claude/settings.hooks.json`. Ne les réécris pas.

## Interview
Lis d'abord : `git status` dans le vault, `.gitignore`, `.claude/settings.json`, la présence de fichiers `*.env`, `*.key`, `credentials*.json` dans le vault (`git ls-files` et recherche de fichiers).

Puis demande :
1. « As-tu déjà un compte GitHub ? » Sinon, guide la création sur github.com (email, mot de passe, code de vérification : ses mains).
2. « Ton ordinateur est allumé à quelles heures ? » Pour caler les sauvegardes (défaut : 4 fois par jour plus à l'ouverture de session).
3. « As-tu des clés ou mots de passe d'outils quelque part dans tes notes ? » S'il y en a, on les déplace avant tout commit.
4. « Des très gros fichiers dans le vault ? » (vidéos, archives). Ils restent hors de git et vont dans sauvegardes-3-lieux.

Range les réponses dans `wiki/maps/securite.md` (dépôt, horaires, emplacement des secrets, exclusions), avec 3 liens.

## Construire
1. **Ranger les secrets (5 min).** Crée `~/.claude/secrets/` (Windows : `%USERPROFILE%\.claude\secrets\`). Un fichier par service, format `NOM=valeur` : `notion.env`, `fathom.env`... Déplace toute clé trouvée dans le vault vers ce dossier. Règle dans le cœur :
   ```markdown
   ## Secrets
   Jamais de clé, jeton ou mot de passe dans le vault ni dans un message. Ils vivent dans
   ~/.claude/secrets/<service>.env. Les scripts les lisent là. Une clé collée dans la conversation
   est considérée comme exposée : propose de la régénérer.
   ```
2. **.gitignore (2 min).** Celui posé par `creer-vault.py` exclut déjà `*.env`, `*.key`, `*.pem`, `secrets/`, `credentials*.json`, les caches, les vidéos. Vérifie qu'il est là. Les gros fichiers (vidéos, archives) restent hors de git.
3. **Git local (3 min).**
   ```bash
   git init
   git add -A
   git status --short     # relis la liste : aucun secret, aucune vidéo
   git commit -m "Premier état du vault"
   ```
4. **GitHub privé (5 min, ses mains pour la connexion).**
   ```bash
   gh auth login           # GitHub.com, HTTPS, connexion par le navigateur
   gh repo create mon-vault --private --source . --push
   ```
   Vérifie sur github.com que le dépôt affiche « Private ». Le jeton reste dans le gestionnaire d'identifiants du système, jamais dans `.git/config`.
5. **Script de sauvegarde (3 min).** Copie `outils/sauvegarde-git.py` vers `scripts/`. Essai :
   ```bash
   python scripts/sauvegarde-git.py --verif
   python scripts/sauvegarde-git.py
   ```
   Il refuse de pousser si un secret est suivi (code 3), retire un verrou git orphelin, commite, fait `pull --rebase --autostash`, pousse avec 3 essais, et écrit `outputs/.derniere-sauvegarde-git-ok`.
6. **Planifier (10 min).** Windows (PowerShell, une fois) :
   ```powershell
   $v = "C:\chemin\du\vault"
   $a = New-ScheduledTaskAction -Execute "python" -Argument "scripts\sauvegarde-git.py" -WorkingDirectory $v
   $t = @(New-ScheduledTaskTrigger -Daily -At 4am), (New-ScheduledTaskTrigger -Daily -At 10am),
        (New-ScheduledTaskTrigger -Daily -At 4pm), (New-ScheduledTaskTrigger -Daily -At 10pm),
        (New-ScheduledTaskTrigger -AtLogOn)
   Register-ScheduledTask -TaskName "Sauvegarde vault GitHub" -Action $a -Trigger $t -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
   ```
   Mac et Linux (`crontab -e`) :
   ```bash
   0 4,10,16,22 * * * cd "/chemin/du/vault" && /usr/bin/env python3 scripts/sauvegarde-git.py >> outputs/sauvegarde-git.log 2>&1
   ```
7. **Hook anti-suppression (5 min).** Si bibliothecaire-installer ne l'a pas déjà fait : copie `.claude/hooks/anti-suppression.js` du socle et fusionne l'entrée `PreToolUse` de `.claude/settings.hooks.json` dans `.claude/settings.json`. Vérifie :
   ```bash
   echo '{"tool_name":"Bash","tool_input":{"command":"git reset --hard"}}' | node .claude/hooks/anti-suppression.js; echo "code $?"
   ```
   Code 2 attendu. Le hook propose à Claude une alternative sûre (corbeille, `git stash`).

## Test
`python scripts/sauvegarde-git.py --verif` affiche « Aucun secret suivi par git », la tâche planifiée a tourné au moins une fois (date récente dans `outputs/.derniere-sauvegarde-git-ok`), le dernier commit apparaît sur github.com dans un dépôt « Private », et le hook bloque `rm -rf` avec le code 2.

## Pièges vécus
- Réécrire l'historique git pour alléger un dépôt devenu lourd : risque de tout casser. Règle : ne jamais réécrire l'historique. Si le dépôt pose problème, nouveau dépôt depuis l'état actuel, l'ancien archivé en lecture seule.
- Vidéos commitées : le dépôt a pris plusieurs gigaoctets qu'on ne peut plus retirer sans réécrire l'historique. Les vidéos sont exclues dès le premier jour.
- Jeton GitHub écrit dans `.git/config` d'un dossier synchronisé : fuite possible. `gh auth login` garde le jeton hors du vault.
- Sauvegarde qui échouait parce qu'une autre tâche écrivait au même moment : `--autostash` et les 3 essais règlent ça.
- Verrou `index.lock` laissé par un git planté : plus aucune sauvegarde pendant des jours sans que personne ne le voie. Le script le retire après 10 minutes, et le marqueur de date permet à un gardien (bloc F) de crier si la dernière sauvegarde est trop vieille.

## Entretien dans le temps
Un gardien (bloc F) vérifie chaque jour que `outputs/.derniere-sauvegarde-git-ok` a moins de 24 heures et notifie sinon. Chaque nouveau service ajoute son fichier dans `~/.claude/secrets/`, jamais ailleurs.

## Après
Coche la ligne `securite-git-secrets` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose memoire-fichiers (ou sauvegardes-3-lieux si le reste du bloc est fait).
