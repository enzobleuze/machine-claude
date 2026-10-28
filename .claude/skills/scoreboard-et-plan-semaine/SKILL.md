---
name: scoreboard-et-plan-semaine
description: "Installe le rythme de la semaine : le scoreboard du dimanche (trois chiffres au plus, une réponse en trente secondes sur Telegram) et le plan du lundi (la semaine écrite par Claude à partir du plan unique, des chiffres et du scoreboard). Utiliser quand l'utilisateur dit « aide-moi à tenir ma semaine », « fais-moi un scoreboard », « prépare ma semaine chaque lundi ». Pas pour l'audit de vie complet (utiliser revue-de-vie)."
---
# Scoreboard du dimanche et plan du lundi

## Pourquoi
Le fondateur d'origine construisait beaucoup et mesurait peu ce qui fait vraiment avancer sa vie et son business. Un message le dimanche avec trois questions chiffrées, auquel il répond directement dans Telegram, a remplacé les tableaux qu'il ne remplissait jamais. Le lundi, Claude écrit la semaine à partir de ces chiffres et du plan unique, avec au moins une action de vente. La leçon : peu de chiffres, une réponse facile, et des actions envers des gens plutôt que des promesses à soi-même.

## Prérequis
- notifications-telegram (niveau `hebdo`), wrapper-de-tache, taches-planifiees.
- Le plan unique du bloc D (sinon le plan du lundi s'appuie sur `wiki/maps/parcours.md`).
- Pour lire la réponse Telegram en session : le plugin Telegram officiel de Claude Code, ou l'utilisateur recopie sa réponse.

## Interview
Lis d'abord : le plan unique, le dernier audit de `revue-de-vie` s'il existe, `wiki/maps/automatisations.md`, et la mémoire sur le rythme de l'utilisateur.
Puis demande :
1. « Quels sont les trois chiffres qui, s'ils montent, font avancer ta vie ? Un pour le business, un ou deux pour toi. » Propose des exemples : conversations de vente engagées, séances de sport, couchers à l'heure. Refuse plus de trois.
2. « Quel jour et quelle heure pour te les demander ? » (défaut dimanche 18 h).
3. « Le lundi, à quelle heure veux-tu trouver ta semaine prête ? »
4. « Combien d'heures as-tu vraiment cette semaine pour le business ? » (à redemander chaque lundi si ça varie).
Range les questions dans `wiki/maps/scoreboard.md` (section « Questions ») et l'historique des réponses dans la même page (tableau daté).

## Construire
1. **Page du scoreboard (Claude, 5 min).** `wiki/maps/scoreboard.md` avec la section « Questions » (les trois questions, numérotées) et un tableau « semaine, chiffre 1, chiffre 2, chiffre 3, note ».
2. **Script du dimanche (Claude, 5 min).** `scripts/scoreboard.sh` :
   ```bash
   #!/usr/bin/env bash
   . "$(dirname "$0")/env.sh"
   Q="$(sed -n '/^## Questions/,/^## /p' wiki/maps/scoreboard.md | grep -E '^[0-9]+\.')"
   [ -n "$Q" ] || exit 1
   notifier hebdo "Scoreboard de la semaine" "Réponds ici en 30 secondes (format : 0 / 2 / 4) :
   $Q"
   ```
3. **Planifier le dimanche (Claude, 2 min).** Windows : `planifier-tache.ps1 -Nom scoreboard -Commande "bash scripts/scoreboard.sh" -Heure 18:00 -Jours Sunday`. Mac et Linux : `planifier-tache.sh --nom scoreboard --commande "bash scripts/scoreboard.sh" --heure 18:00 --jours 0`.
4. **Script du lundi (Claude, 10 min).** `scripts/plan-semaine.sh` :
   ```bash
   #!/usr/bin/env bash
   . "$(dirname "$0")/env.sh"
   OUT="outputs/plan-semaine/$(date +%F).md"; mkdir -p outputs/plan-semaine
   claude_tache "Écris $OUT : la semaine qui commence. Lis le plan unique, wiki/maps/scoreboard.md,
   les rapports du matin des 7 derniers jours et les tâches ouvertes. Donne : le cap de la semaine en une phrase,
   deux chantiers au plus, au moins une action de vente ou de contact avec un client, un plancher minimal pour chaque
   chantier (ce qui compte comme fait même un mauvais jour), et ce qui est volontairement reporté.
   Français simple, listes de 5 points au plus." --allowedTools "Read,Write,Glob,Grep" || exit 1
   [ -s "$OUT" ] || exit 1
   notifier hebdo "Ta semaine est prête" "Ouvre $OUT ou dis « plan de la semaine » en session."
   ```
   Planifie-le le lundi matin (`-Jours Monday`, `--jours 1`). Ajoute les deux tâches au gardien (170 heures).
5. **Lire la réponse (Claude, en session, 2 min).** À la première session après le dimanche : lis la réponse (plugin Telegram ou recopiée), ajoute la ligne dans le tableau de `wiki/maps/scoreboard.md`, et dis en une phrase la tendance sur trois semaines.

## Test
Le dimanche à l'heure dite, le message arrive sur le téléphone avec les trois questions. Le lundi, `outputs/plan-semaine/<date>.md` existe et contient au moins une action de vente et un plancher par chantier.

## Pièges vécus
- **Trop de chiffres** : personne ne répond à dix questions. Trois au plus, et une réponse en trente secondes.
- **Plans maximalistes** : un plan « à fond » fige quelqu'un qui fonctionne par pics. Chaque chantier a un plancher ridicule et tenable ; les pics restent des bonus.
- **Engagements envers soi seul** : ils tiennent mal. Le plan met en avant des engagements envers des gens (un appel réservé, une réponse attendue).
- **Construire au lieu de vendre** : dès que le business existe, au moins la moitié du temps va à servir et vendre. Le plan du lundi le vérifie.
- **Plus de deux chantiers** : au-delà, rien n'avance. Le plan reporte le reste par écrit.

## Entretien dans le temps
Toutes les quatre semaines, relis le tableau : un chiffre qui ne bouge jamais ou qui ne sert à aucune décision est remplacé, avec l'accord de l'utilisateur. La revue de vie mensuelle s'appuie sur ce tableau.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Note en mémoire les trois chiffres choisis et l'heure du scoreboard. Propose ensuite journal-coach.
