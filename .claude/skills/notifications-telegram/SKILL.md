---
name: notifications-telegram
description: "Branche les notifications de la machine sur un bot Telegram avec une règle stricte : le téléphone ne sonne que quand l'humain doit agir et que Claude ne peut pas régler seul ; tout le reste va dans un résumé du jour lu par Claude en session. Utiliser quand l'utilisateur dit « préviens-moi sur mon téléphone », « trop de notifications », « branche Telegram ». Pas pour discuter avec Claude depuis le téléphone (c'est le plugin Telegram officiel, brique à part)."
---
# Notifications Telegram

## Pourquoi
Le système d'origine a commencé par tout notifier : démarrages, succès, étapes. Le fil a dépassé deux cents messages non lus et le fondateur ne regardait plus rien, donc les vraies pannes passaient aussi. Trois régimes successifs ont mené à la règle finale, dite par lui : être notifié seulement si la machine ou le business a besoin de lui et que ça ne peut pas se régler tout seul. Le reste s'écrit dans un résumé du jour que Claude lit en début de session et répare lui-même.

## Prérequis
- wrapper-de-tache (`notify.sh` et `notify.py` copiés dans `scripts/`).
- Un compte Telegram sur le téléphone (gratuit).

## Interview
Lis d'abord : `wiki/maps/automatisations.md`, et cherche dans `scripts/` les anciens appels de notification (email, ntfy, autre) à remplacer.
Puis demande :
1. « Tu as Telegram sur ton téléphone ? Sinon, installe-le, je t'attends. »
2. « Y a-t-il un message que tu veux recevoir même quand tout va bien ? Par exemple le scoreboard du dimanche ou le plan du lundi. » (ce sont les seuls messages `hebdo`).
3. « Qu'est-ce qui, chez toi, mérite vraiment de te réveiller ? » Donne des exemples : un compte à reconnecter, la sauvegarde morte, un paiement refusé.
Range la liste des cas `urgent` et des messages `hebdo` dans `wiki/maps/notifications.md`.

## Construire
1. **Créer le bot (l'utilisateur, 5 min, guidé).** Dans Telegram : cherche `@BotFather`, tape `/newbot`, donne un nom, puis un identifiant qui finit par `bot`. BotFather répond avec un jeton. Copie-le dans `~/.claude/secrets/telegram.env` sur une ligne `TELEGRAM_BOT_TOKEN=...`. Ne le colle jamais dans la conversation.
2. **Trouver l'identifiant de discussion (l'utilisateur puis Claude, 3 min).** L'utilisateur envoie « bonjour » à son bot. Ensuite il ouvre dans son navigateur `https://api.telegram.org/bot<jeton>/getUpdates` et copie le nombre après `"chat":{"id":`. Il l'ajoute dans le même fichier : `TELEGRAM_CHAT_ID=...`.
3. **Essai à blanc (Claude, 1 min).** `NOTIFY_SIMULER=1 bash scripts/notify.sh urgent "Essai" "Ceci est un test"` affiche le message sans l'envoyer.
4. **Vrai essai (Claude, avec l'accord de l'utilisateur, 1 min).** `bash scripts/notify.sh urgent "Essai" "Si tu lis ça, la machine sait te joindre."` L'utilisateur confirme la réception. Si rien n'arrive, lis la ligne `[SENDFAIL]` dans `outputs/cron-logs/resume-<date>.log`.
5. **Remplacer les anciens appels (Claude, 15 min).** Tout script qui notifiait autrement appelle désormais `notifier <niveau> "<titre>" "<message>"` (bash) ou `notifier(...)` (Python). Aucun script n'appelle l'API Telegram directement.
6. **Écrire la règle (Claude, 5 min).** Dans `wiki/maps/notifications.md` : le tableau des niveaux ci-dessous et la liste des cas `urgent`.

| Niveau | Va où | Pour quoi |
|---|---|---|
| `urgent` | téléphone, avec son | l'humain doit agir et Claude ne peut pas régler seul |
| `hebdo` | téléphone, sans son | seulement les messages demandés par l'humain |
| `warn` | résumé du jour | panne que Claude réparera en session |
| `info`, `ok` | résumé du jour | routine, succès |
| `silent` | nulle part | rien |

Règle pour tout nouveau code : `info` par défaut. `urgent` seulement si un cas de la liste s'applique. Chaque message dit en langage simple ce qui se passe et quoi faire, en une ou deux phrases.

## Test
`NOTIFY_SIMULER=1 bash scripts/notify.sh warn "x" "y"` n'affiche rien et ajoute une ligne `[warn]` au résumé du jour. Le vrai essai `urgent` de l'étape 4 arrive sur le téléphone avec son.

## Pièges vécus
- **Trop de messages = plus aucun message lu.** Couper le son ne suffit pas, il faut couper l'envoi. La règle vit dans le transport (`notify.sh`), donc aucun appelant n'a à y penser.
- **Accents et emojis cassés sous Windows** : `curl.exe` abîme les caractères passés en argument. Le texte passe par l'entrée standard, jamais en argument.
- **Envoi perdu en silence** : la réponse de Telegram est vérifiée, un nouvel essai part après quelques secondes, et un échec définitif laisse `[SENDFAIL]` dans le résumé.
- **Jeton du bot vu dans une conversation** : il faut le changer. BotFather, `/mybots`, ton bot, « Revoke », puis mets à jour `telegram.env`.
- **Une notification qui casse la tâche** : `notifier` rend toujours 0. Une panne réseau ne doit jamais arrêter une sauvegarde.

## Entretien dans le temps
Le rapport du matin compte les lignes `warn`, `urgent` et `SENDFAIL` du résumé. Chaque fois que l'utilisateur dit « encore une notif inutile », rétrograde ce cas d'un niveau et note-le dans `wiki/maps/notifications.md`. Chaque fois qu'il découvre une panne trop tard, ajoute le cas à la liste `urgent` ou au gardien.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Note en mémoire la règle de notification de l'utilisateur, dans ses mots. Propose ensuite rapport-du-matin.
