---
name: sauvegardes-3-lieux
description: "Installe les sauvegardes en trois lieux : GitHub privé (le texte, plusieurs fois par jour), un miroir lisible du vault sur un stockage en ligne avec les anciennes versions gardées, et un coffre chiffré pour ~/.claude (mémoire, skills, secrets) et les fichiers sensibles. Utiliser quand l'utilisateur dit « si mon ordinateur grille je perds tout ? », « sauvegarde complète », « coffre chiffré ». Pas pour git et les secrets eux-mêmes (utiliser securite-git-secrets d'abord)."
---
# Sauvegardes en trois lieux

## Pourquoi
Dans le système d'origine, GitHub gardait le texte du vault mais pas le reste : la mémoire de Claude, les skills et les secrets dans `~/.claude`, les vidéos, les gros fichiers hors git. Un disque mort aurait effacé des mois de réglages. Trois lieux ont réglé ça : GitHub pour l'historique du texte, un miroir lisible sur un stockage en ligne pour tout le vault avec chaque version modifiée gardée par date, et un coffre chiffré pour ce qui ne doit jamais être lisible en clair. Leçon vécue : garder les versions trop peu de temps ne protège pas d'une erreur découverte tard, le fondateur a choisi deux ans.

## Prérequis
- securite-git-secrets fait (GitHub privé en place, secrets dans `~/.claude/secrets/`).
- Un stockage en ligne : Google Drive (souvent déjà payé avec de l'espace), ou un autre que rclone sait joindre (Dropbox, un stockage objet type S3). Coût éventuel : l'espace de stockage.
- rclone (gratuit). Windows : `winget install Rclone.Rclone`. Mac : `brew install rclone`.
- Python 3.9+.

## Interview
Lis d'abord : `wiki/maps/securite.md`, la taille du vault (`du -sh .` ou propriétés du dossier) et de `~/.claude`.

Puis demande :
1. « Quel stockage en ligne as-tu, et combien de place libre ? »
2. « Combien de temps garder les anciennes versions ? » Défaut conseillé : 730 jours.
3. « Y a-t-il des fichiers sensibles hors du vault à protéger ? » (vidéos clients, documents d'identité). Ils iront dans le coffre chiffré.
4. « As-tu un gestionnaire de mots de passe ? » Le mot de passe du coffre y sera rangé. Sans lui, le coffre est perdu.

Range les réponses dans `wiki/maps/securite.md` (section sauvegardes : lieux, durée, contenu du coffre, où est rangé le mot de passe sans jamais l'écrire).

## Construire
1. **Distant en ligne (10 min, ses mains pour la connexion).** `rclone config` > `n` (nouveau) > nom `gdrive` > type `drive` > laisser client_id vide > scope `drive.file` (rclone ne voit que ce qu'il crée : rien d'autre du Drive n'est exposé) > connexion par le navigateur. Vérifie : `rclone lsd gdrive:`.
2. **Coffre chiffré (10 min).** `rclone config` > `n` > nom `coffre` > type `crypt` > remote `gdrive:Sauvegardes/03-coffre` > chiffrer les noms de fichiers : oui > mot de passe : la personne en choisit un long et le range dans son gestionnaire, deuxième mot de passe (sel) aussi. Claude ne voit pas ces valeurs : la personne les tape elle-même dans le terminal.
   Écris dans `~/.claude/secrets/sauvegarde.md` seulement l'endroit où le mot de passe est rangé (« gestionnaire, entrée Coffre vault »), jamais le mot de passe.
3. **Outils (2 min).** Copie `outils/sauvegarde-drive.py` et `outils/filtre-sauvegarde.txt` vers `scripts/`. Le filtre exclut `.git`, les secrets, les caches.
4. **Essai à blanc (5 min).**
   ```bash
   python scripts/sauvegarde-drive.py --distant gdrive --coffre coffre --essai
   ```
   Relis la liste avec la personne : aucun `.env`, aucun dossier secrets dans la partie miroir.
5. **Premier envoi (selon la taille, laisse tourner).** Même commande sans `--essai`. Résultat dans le Drive : `Sauvegardes/01-vault` (miroir lisible), `Sauvegardes/03-coffre` (illisible sans mot de passe), et plus tard `Sauvegardes/04-versions/AAAA-MM-JJ_HHMM/` pour chaque fichier modifié ou supprimé.
6. **Mode d'emploi (3 min).** Écris `Sauvegardes/LISEZMOI.md` sur le Drive (par `rclone copyto`) : ce que contient chaque dossier, comment restaurer (`rclone copy gdrive:Sauvegardes/01-vault <dossier>` ; coffre : `rclone copy coffre:claude ~/.claude`), où est le mot de passe.
7. **Planifier la nuit (10 min).** Une fois par nuit, après le jardinier. Windows :
   ```powershell
   $v = "C:\chemin\du\vault"
   $a = New-ScheduledTaskAction -Execute "python" -Argument "scripts\sauvegarde-drive.py --distant gdrive --coffre coffre --garde 730" -WorkingDirectory $v
   Register-ScheduledTask -TaskName "Sauvegarde vault Drive" -Action $a -Trigger (New-ScheduledTaskTrigger -Daily -At 4:45am) -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
   ```
   Mac et Linux (`crontab -e`) :
   ```bash
   45 4 * * * cd "/chemin/du/vault" && /usr/bin/env python3 scripts/sauvegarde-drive.py --distant gdrive --coffre coffre --garde 730 >> outputs/sauvegarde-drive.log 2>&1
   ```
   rclone doit être dans le PATH de la tâche : sinon, mets son chemin complet (`where rclone` ou `which rclone`) dans la commande.
8. **Exercice de restauration (10 min, une fois).** Restaure un fichier du miroir et un fichier du coffre dans un dossier temporaire, compare avec l'original. Une sauvegarde jamais restaurée n'est pas une sauvegarde prouvée.

## Test
`outputs/.derniere-sauvegarde-drive-ok` a moins de 24 heures, `rclone lsd gdrive:Sauvegardes` montre `01-vault` et `03-coffre`, `rclone ls gdrive:Sauvegardes/01-vault | grep -i "\.env"` ne renvoie rien, et l'exercice de restauration a réussi.

## Pièges vécus
- `~/.claude` sans aucune copie : mémoire, skills et secrets n'existaient qu'à un seul endroit. Il va dans le coffre chiffré.
- Miroir qui recopiait aussi les suppressions : un fichier effacé par erreur disparaissait aussi de la sauvegarde. `--backup-dir` le garde dans `04-versions/` avant de le retirer du miroir.
- Durée de versions trop courte : une erreur vue après trois mois n'était plus réparable. Deux ans par défaut, purge seulement par le nom daté des dossiers.
- Mot de passe du coffre gardé seulement sur l'ordinateur : perdu avec lui. Il vit dans le gestionnaire de mots de passe.
- Secrets envoyés en clair dans le miroir faute de filtre : le script refuse de tourner sans le fichier filtre.

## Entretien dans le temps
Le gardien du bloc F vérifie chaque jour les deux marqueurs (`.derniere-sauvegarde-git-ok`, `.derniere-sauvegarde-drive-ok`) et notifie seulement si l'un a plus de 24 heures. Un exercice de restauration tous les six mois.

## Après
Coche la ligne `sauvegardes-3-lieux` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose les ingestions de sources qui manquent (Drive, Notion, appels, réseaux, articles) ou passe au bloc B.
