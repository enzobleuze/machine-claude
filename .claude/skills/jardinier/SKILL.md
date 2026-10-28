---
name: jardinier
description: "Installe le jardinier : une tâche de nuit sans IA (coût nul) qui complète les frontmatter, régénère le catalogue de index.md, archive le journal par trimestre, déplace les vieux fichiers vers l'archive, compte liens morts et orphelines, puis fait un seul commit. Utiliser quand l'utilisateur dit « le wiki doit s'entretenir seul », « installe le jardinier », « brique ». Pas pour un bilan ponctuel (utiliser lint-wiki)."
---
# Le jardinier (entretien de nuit)

## Pourquoi
Dans le système d'origine, le wiki grossissait plus vite qu'on ne pouvait le ranger : frontmatter oubliés, index en retard, journal de plusieurs centaines de Ko. Un ancien contrôle hebdomadaire produisait des rapports que personne ne lisait. Le jardinier a remplacé ça par un entretien qui agit : déterministe d'abord (presque tout se règle en Python sans IA, donc sans coût), un seul commit par nuit pour pouvoir tout défaire, et une période de rodage à blanc avant d'écrire pour de vrai. L'IA n'intervient qu'une fois par semaine, en option, pour les cas qui demandent du jugement.

## Prérequis
- architecture-vault, lint-wiki (le jardinier importe `scripts/lint_wiki.py`), securite-git-secrets (dépôt git en place).
- Python 3.9+.
- Tâches planifiées : le Planificateur de tâches sous Windows, `launchd` ou `cron` sur Mac et Linux. Le bloc F détaille les tâches planifiées ; ce skill suffit pour celle-ci.

## Interview
Lis d'abord : `wiki/maps/architecture.md` (zones privées), `wiki/maps/lint.md`, la taille de `log.md`, les dossiers de `wiki/` qui accumulent des fichiers datés (rapports, audits, briefings).

Puis demande :
1. « À quelle heure ton ordinateur est allumé mais tu ne travailles pas ? » Défaut : 3 h du matin. S'il est éteint la nuit, choisis le midi ou « à l'ouverture de session ».
2. « Y a-t-il des dossiers de rapports qui peuvent partir en archive après un certain temps ? » Ex. rapports d'audit après 60 jours.
3. « Tu veux un résumé le matin, ou seulement s'il y a un problème ? » Défaut : seulement en cas de problème (le résumé reste dans `outputs/jardinier/`).

Range les réponses dans `scripts/jardinier.json` et `wiki/maps/jardinier.md` (heure, règles d'archivage, mode de résumé, 3 liens).

## Construire
1. **Outil (2 min).** Copie `outils/jardinier.py` vers `scripts/`, à côté de `scripts/lint_wiki.py`. Vérifie : `python scripts/jardinier.py --test`.
2. **Configuration (3 min).** `scripts/jardinier.json` :
   ```json
   {
     "prives": ["wiki/finances"],
     "archivage": [
       {"dossier": "wiki/audits", "age_jours": 60}
     ]
   }
   ```
   Les dossiers privés ne sont jamais modifiés. L'archivage DÉPLACE vers `wiki/archive/...` et corrige les liens écrits avec le chemin complet.
3. **Rodage (2 min).** Crée le fichier vide `.jardinier-rodage` à la racine du vault. Tant qu'il existe, `--live` est ignoré : le jardinier montre ce qu'il ferait sans rien écrire.
4. **Premier passage à blanc (3 min).** `python scripts/jardinier.py` puis lis `outputs/jardinier/AAAA-MM-JJ.md` avec la personne.
5. **Tâche planifiée (10 min).** Commande à planifier : `python scripts/jardinier.py --live --commit`, lancée depuis la racine du vault.
   Windows (PowerShell, une fois) :
   ```powershell
   $v = "C:\chemin\du\vault"
   $a = New-ScheduledTaskAction -Execute "python" -Argument "scripts\jardinier.py --live --commit" -WorkingDirectory $v
   $t = New-ScheduledTaskTrigger -Daily -At 3am
   $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun
   Register-ScheduledTask -TaskName "Jardinier du vault" -Action $a -Trigger $t -Settings $s
   ```
   Si `python` n'est pas trouvé par la tâche, mets le chemin complet donné par `(Get-Command python).Source`.
   Mac et Linux (`crontab -e`, une ligne) :
   ```bash
   0 3 * * * cd "/chemin/du/vault" && /usr/bin/env python3 scripts/jardinier.py --live --commit >> outputs/jardinier/cron.log 2>&1
   ```
   Sur Mac, si cron n'a pas accès au dossier : Réglages Système > Confidentialité > Accès complet au disque > ajouter `/usr/sbin/cron`.
6. **Fin du rodage (après 2 nuits propres, 1 min).** Relis les deux résumés avec la personne. S'ils sont justes, retire `.jardinier-rodage`.
7. **Étapes facultatives (5 min chacune).** Ajoute à la même tâche, dans un petit script `scripts/nuit.sh` ou `scripts/nuit.ps1` qui les enchaîne : `python scripts/cerveau-check.py` (test d'or de la recherche), `python scripts/memoire-check.py` le 1er du mois, `python scripts/articles-db.py`. Chaque étape qui échoue est notée, aucune ne fait tomber les autres.
8. **Jugement hebdomadaire (optionnel, bloc B pour `claude -p`).** Une fois par semaine, une session sans fenêtre lit le résumé et propose un rattachement pour chaque orpheline. Règle : l'IA propose, un script vérifie que la page cible existe avant d'écrire, et l'IA ne modifie jamais un fichier elle-même.

## Test
Après la première nuit en écriture : `outputs/jardinier/<date>.md` existe avec le mode « écriture », `git log -1` montre « jardinier: entretien <date> », et `python scripts/lint_wiki.py --json` montre zéro frontmatter incomplet hors zones privées.

## Pièges vécus
- Rapports passifs que personne ne lit : remplacés par des réparations réelles et un résumé court.
- Écriture directe sans rodage : un bug aurait touché tout le wiki d'un coup. Le fichier de rodage et le commit unique par nuit rendent tout réversible.
- Frontmatter écrasé : interdit. Le jardinier ajoute seulement les clés absentes.
- Zone privée envoyée à une IA ou modifiée par erreur : la liste `prives` est lue avant toute action.
- Tâche lancée avec un autre Python que celui des outils : modules introuvables. Utilise le chemin complet du bon Python.
- Ordinateur en veille à l'heure prévue : `-StartWhenAvailable` (Windows) rattrape le passage manqué ; sur Mac, préfère `launchd` qui rattrape aussi.

## Entretien dans le temps
Lis le résumé quand une alerte arrive, ou une fois par semaine en session. Si le même problème revient trois nuits de suite, c'est une règle à ajouter au jardinier ou à `wiki/maps/lint.md`.

## Après
Coche la ligne `jardinier` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose fin-de-session.
