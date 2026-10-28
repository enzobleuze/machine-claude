---
name: rapport-du-matin
description: "Produit chaque matin un rapport court : ce que la machine a fait seule, ce que l'humain doit faire (trois actions au plus, avec les minutes), et les alertes. Les faits sont rassemblés par un script, la rédaction par Claude. Utiliser quand l'utilisateur dit « fais-moi un point chaque matin », « qu'est-ce qui s'est passé cette nuit », « le brief du matin ». Pas pour les chiffres du business (utiliser le cockpit du bloc D)."
---
# Rapport du matin

## Pourquoi
Avec des dizaines de tâches, personne ne peut lire les journaux. Dans le système d'origine, un bilan quotidien envoyé sur le téléphone a d'abord aidé, puis il est devenu du bruit : le fondateur l'a fait supprimer du téléphone. Ce qui est resté : un fichier du matin dans le vault, au format fixe (TL;DR, AUTO, TOI, ALERTE), que Claude complète et présente à l'ouverture de la première session. Le téléphone ne sonne que si une action urgente attend.

## Prérequis
- wrapper-de-tache, gardien, notifications-telegram.
- La brique « format de sortie » du bloc B (TL;DR, AUTO, TOI, ALERTE).
- Coût : un appel `claude -p` court par jour.

## Interview
Lis d'abord : `wiki/maps/automatisations.md`, le format de sortie dans `CLAUDE.md`, le plan en cours (`wiki/maps/plan.md` ou équivalent du bloc D), et les trois derniers rapports s'il y en a.
Puis demande :
1. « À quelle heure tu lis ton premier écran le matin ? » (le rapport est prêt une demi-heure avant).
2. « Combien de minutes maximum veux-tu passer sur ce que je te demande chaque jour ? » (sert à limiter la section TOI).
3. « Le rapport s'ouvre tout seul en début de session, ou tu le demandes ? »
Range les réponses dans `wiki/maps/automatisations.md` (section « Matin ») et en mémoire.

## Construire
1. **Copier le script des faits (Claude, 2 min).** `outils/rapport-du-matin.py` vers `scripts/`. Auto-test : `python scripts/rapport-du-matin.py --selftest`.
2. **Script de la tâche (Claude, 10 min).** `scripts/rapport-du-matin.sh` :
   ```bash
   #!/usr/bin/env bash
   . "$(dirname "$0")/env.sh"
   F="$("$PYTHON" scripts/rapport-du-matin.py)" || exit 1
   claude_tache "Lis $F (section Faits), la fin de log.md et le plan en cours. Au-dessus du bloc FAITS, écris :
   un TL;DR de 3 lignes, AUTO (ce que la machine a fait seule), TOI (3 actions au plus, chacune avec ses minutes,
   jamais une micro-étape que tu peux faire toi-même), ALERTE (ou « rien »). Français simple, listes de 5 points au plus.
   Ne touche pas au bloc FAITS. Si le fichier a déjà un TL;DR écrit par une session, complète-le au lieu d'en écrire un second." \
     --allowedTools "Read,Edit,Glob,Grep" || exit 1
   grep -q "TL;DR" "$F" || exit 1
   ```
3. **Planifier (Claude, 2 min).** Une demi-heure avant le réveil : `planifier-tache.ps1 -Nom rapport-du-matin -Commande "bash scripts/rapport-du-matin.sh" -Heure 06:30` (Mac et Linux : `planifier-tache.sh`). Ajoute au gardien : `outputs/brief-matin/{date}.md`.
4. **Lecture en session (Claude, 5 min).** Ajoute dans `CLAUDE.md` : « Première session du jour : lis `outputs/brief-matin/<date>.md` et le résumé `outputs/cron-logs/resume-<date>.log`, répare ce qui est en `warn` sans attendre, puis présente le rapport. »
5. **Alerte téléphone (Claude, 2 min).** Rien à faire : seuls les `urgent` de la nuit ont déjà sonné. Le rapport ne s'envoie pas sur Telegram, sauf si l'utilisateur l'a demandé (niveau `hebdo`).

## Test
Le fichier `outputs/brief-matin/<date>.md` existe avant l'heure de réveil, contient TL;DR, AUTO, TOI et ALERTE, et le bloc FAITS reste intact après un second passage du script.

## Pièges vécus
- **Rapport envoyé chaque jour sur le téléphone** : vite ignoré. Il vit dans le vault, la session le présente.
- **Deux rapports le même matin** : une session de nuit et la tâche en écrivaient chacune un. Un seul fichier par jour, complété, jamais doublé.
- **Section TOI trop longue** : un plan maximaliste fige. Trois actions au plus, chacune minutée, et Claude fait tout ce qu'il peut faire seul.
- **Rédaction sans faits** : un modèle invente des réussites. Le script rassemble les faits d'abord ; la rédaction ne fait que les mettre en mots.

## Entretien dans le temps
Si l'utilisateur saute la section TOI plusieurs jours de suite, réduis-la à une action. Si une alerte revient trois matins de suite, transforme-la en tâche dans le gestionnaire de tâches du bloc B.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Note en mémoire l'heure de lecture et le budget de minutes. Propose ensuite scoreboard-et-plan-semaine.
