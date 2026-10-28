---
name: claude-sans-fenetre
description: "Met en place Claude sans fenêtre (claude -p, lancé par un script ou une tâche planifiée) avec le jeton longue durée, les réglages d'appel allégé et l'essai qui prouve que ça marche la nuit. Utiliser quand l'utilisateur dit « je veux que Claude travaille la nuit », « mes tâches automatiques ne marchent pas », « erreur 401 la nuit », « Not logged in », « appelle Claude depuis un script ». Pas pour l'enveloppe commune des tâches (utiliser wrapper-de-tache) ni pour l'horaire (utiliser taches-planifiees)."
---
# Claude sans fenêtre et jeton longue durée

## Pourquoi
Toute l'automatisation du système d'origine (articles, posts, veille, entretien du wiki) passe par `claude -p` : Claude lancé par un script, sans conversation. Une nuit, tous les appels ont répondu « 401 » : le jeton de connexion de l'app expirait vite et ne se rafraîchissait pas pour les scripts. Le moteur de contenu est mort en silence jusqu'au matin. Le jeton longue durée a réglé ça pour un an. Ensuite, des réglages d'appel allégé ont divisé plusieurs fois le coût fixe de chaque appel.

## Prérequis
- couts-et-limites (comprendre que ces appels consomment le même forfait).
- La commande `claude` dans un terminal normal (`claude --version`).
- Windows : Git Bash pour la version `.sh`, ou PowerShell pour la version `.ps1`.
- Ensuite, au bloc F : wrapper-de-tache (l'enveloppe commune) et taches-planifiees (l'horaire). Cette brique-ci prépare seulement l'appel et le jeton.

## Interview
Lis d'abord : `wiki/maps/couts.md`, `scripts/` (des scripts appellent-ils déjà `claude -p` ?), `log.md` (incidents la nuit). Ne lis jamais le contenu de `~/.claude/secrets/` : vérifie seulement si le fichier existe.

Puis demande :
1. « Quel travail tu aimerais que Claude fasse sans toi, pendant que tu dors ou que tu es ailleurs ? » (donne les premiers cas d'usage, rangés dans `wiki/maps/automatisations.md`).
2. « Ton ordinateur reste-t-il allumé la nuit ? » (sinon, les tâches tournent à l'allumage ; voir le bloc F).
3. « As-tu une clé API Anthropic ? » (si oui, rappelle qu'elle se facture à part).

## Construire

1. **Ce que fait `claude -p` (3 min).** Claude explique : `claude -p "<consigne>"` lance Claude une fois, sans fenêtre, dans le dossier courant, avec le même CLAUDE.md, la même mémoire et les mêmes connecteurs qu'une session, puis s'arrête. Options utiles :
   | Option | Rôle |
   |:-|:-|
   | `--model sonnet` | modèle de l'appel (le moyen par défaut pour la nuit) |
   | `--output-format json` | sortie lisible par un script, avec coût et jetons |
   | `--max-turns N` | borne le nombre de tours |
   | `--allowedTools "Read,Write"` | outils permis sans demander (sinon l'appel bloque sur une permission) |
   | `--strict-mcp-config` | ne charge aucun connecteur (sans `--mcp-config`), pour un appel qui n'en a pas besoin |

2. **Créer le jeton longue durée (la personne, 3 min).** Guide-la : ouvrir un terminal normal (PAS dans Claude Code), taper `claude setup-token`, suivre le lien dans le navigateur, accepter. Le terminal affiche un jeton. Elle crée le fichier `~/.claude/secrets/claude-oauth-token.env` (sur Windows : `C:\Users\<nom>\.claude\secrets\`) avec une seule ligne :
   `CLAUDE_CODE_OAUTH_TOKEN=<le jeton>`
   Claude ne lit ni n'affiche ce fichier. Le jeton vaut environ un an : Claude note la date d'expiration dans `wiki/maps/automatisations.md` et crée une tâche de rappel un mois avant (taches-source-unique).

3. **Protéger le secret (2 min).** Claude vérifie que le dossier `~/.claude/secrets/` est hors du vault et que le vault n'a aucune ligne `CLAUDE_CODE_OAUTH_TOKEN` (`git grep -n CLAUDE_CODE_OAUTH_TOKEN` ne trouve que des noms de variable, jamais une valeur).

4. **L'essai (5 min).** Claude copie `outils/essai-claude-p.sh` et `outils/essai-claude-p.ps1` dans `scripts/`, puis lance depuis le vault :
   - Git Bash, Mac, Linux : `bash scripts/essai-claude-p.sh`
   - PowerShell : `powershell -ExecutionPolicy Bypass -File scripts\essai-claude-p.ps1`
   Il doit afficher `OK`, les jetons et l'équivalent en dollars. Puis le même en mode `leger` : les jetons écrits doivent baisser.

5. **La règle des appels allégés (10 min).** Claude écrit dans `wiki/maps/automatisations.md` :
   - Un appel de nuit qui n'utilise aucun connecteur : `--strict-mcp-config`.
   - Un appel dont la consigne contient TOUTES ses règles et qui n'a besoin ni de skill, ni de hook, ni du CLAUDE.md : `--safe-mode` en plus, si `claude --help` le propose (il garde ta connexion normale et saute le reste). Jamais pour un appel qui lance une commande `/...` ou compte sur le cœur.
   - Ne pas utiliser `--bare` sur abonnement : ce mode ignore la connexion par jeton et demande une clé API (facturée à part). Vérifié : il répond « Not logged in ».
   - Un appel allégé qui échoue relance une fois en mode normal.
   - Rien de changeant (heure, compteur) au début de la consigne : ça empêche le cache de servir d'un appel à l'autre.
   - Généraliser un réglage seulement après quelques jours de mesure sans casse sur une seule tâche.

6. **La consigne porte ses règles (5 min).** Un appel de nuit ne suit pas les liens du wiki comme une session. Claude ajoute au cœur : « Les règles critiques d'une tâche de nuit sont copiées dans sa consigne ou son fichier de consigne, pas seulement dans une map. »

7. **Le contrôle du résultat (3 min).** Dans `wiki/maps/automatisations.md` : « Un `claude -p` peut sortir 0 sans avoir produit le fichier attendu. Chaque script vérifie son fichier de sortie et écrit l'échec dans son journal. » L'enveloppe du bloc F (wrapper-de-tache) le fait pour toutes les tâches.

## Test
Les deux sont vrais :
- `bash scripts/essai-claude-p.sh leger` (ou la version PowerShell) affiche `OK` et sort 0.
- Le même essai lancé par une tâche planifiée d'essai (bloc F, ou une tâche manuelle « lancer maintenant ») réussit aussi : le jeton marche hors de la session.

## Pièges vécus
- **Le 401 de la nuit.** Le jeton court de l'app se rafraîchit pour l'app, pas pour les scripts. Redémarrer l'app ne répare rien. Seul le jeton longue durée règle ça ; s'il expire, on le régénère, sans enquêter ailleurs.
- **La tâche qui oublie le jeton.** Un script qui ne chargeait pas l'environnement commun est mort deux semaines de suite (« Not logged in »). Toute tâche passe par la même enveloppe (wrapper-de-tache).
- **Le mauvais dossier.** Lancée depuis le dossier système, une tâche ne trouvait ni le cœur ni les transcriptions. Toujours se placer dans le vault avant l'appel.
- **`--bare` qui ne se connecte pas.** Il semblait parfait pour alléger, mais il refuse la connexion par abonnement. `--safe-mode` fait le même allègement avec la connexion normale.
- **La clé API oubliée dans l'environnement.** Une variable `ANTHROPIC_API_KEY` traînante peut faire payer au tarif public. L'essai le signale.
- **La permission qui bloque la nuit.** Un appel sans `--allowedTools` attend une permission que personne ne donne. Liste les outils permis de chaque tâche.

## Entretien dans le temps
- Un mois avant l'expiration du jeton : la tâche de rappel ; la personne refait l'étape 2.
- Chaque nouvelle tâche de nuit : un essai en mode `leger`, la mesure dans `wiki/maps/couts.md`.

## Après
Coche la ligne `claude-sans-fenetre` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, puis propose la brique suivante : connecteurs-mcp.
