---
name: sous-agents-modeles
description: "Met en place les sous-agents (des Claude à part qui font un morceau de travail et rendent une synthèse) et la règle du choix des modèles (lequel pour quoi, quand déléguer, quand ne pas déléguer). Utiliser quand l'utilisateur dit « tu lis trop de fichiers », « ça coûte trop », « fais-le en parallèle », « quel modèle utiliser », « crée un agent ». Pas pour les tâches de nuit (utiliser claude-sans-fenetre)."
---
# Sous-agents et choix des modèles

## Pourquoi
Dans le système d'origine, la session principale lisait parfois des milliers de lignes pour en tirer trois phrases. Le contexte se remplissait de déchets, la session devenait lente et chère. Déléguer ces lectures à un sous-agent, qui rend seulement la conclusion, a gardé la conversation propre. Un test mesuré a aussi montré qu'un modèle moyen écrivait plus proprement que le plus gros sur certaines règles de style : le choix du modèle se teste, il ne se devine pas.

## Prérequis
- format-et-autonomie fait (la règle « 3 fichiers ou plus part à un sous-agent » est dans le cœur).
- settings-permissions fait.
- Aucun coût en plus de l'abonnement, mais chaque sous-agent consomme le même forfait.

## Interview
Lis d'abord : la section « Autonomie » du `CLAUDE.md`, `.claude/agents/` (agents déjà là, par exemple ceux du bloc C), la clé `env` de `~/.claude/settings.json`, `wiki/maps/moi.md`.

Puis demande :
1. « Quel est ton abonnement Claude ? » (Pro, Max, autre : décide la marge pour paralléliser).
2. « Y a-t-il des textes qui doivent garder ta voix exacte ? » (ceux-là ne partent jamais sur un petit modèle).
3. « Y a-t-il des gros dossiers que je dois souvent fouiller ? » (transcriptions, exports, sources : candidats pour l'agent lecteur).
4. « Un rôle qui revient souvent et qui mérite son propre agent ? » (par exemple un relecteur, un client type : le bloc C en fournit).

Range : la matrice de l'étape 2 dans `wiki/maps/modeles.md`, les agents dans `.claude/agents/`.

## Construire

1. **Quand déléguer (5 min).** Claude ajoute au cœur, section « Autonomie » :
   « Avant de lire beaucoup, demande-toi : ai-je besoin du contenu ou seulement de la conclusion ? Conclusion seulement : sous-agent. Moins de 3 fichiers ou une petite édition : fais-le toi-même, un sous-agent coûterait plus (il relit tout à neuf). Des recherches indépendantes : plusieurs sous-agents lancés dans le même message. »

2. **La matrice des modèles (10 min).** Claude écrit `wiki/maps/modeles.md` avec ce tableau, adapté à l'abonnement :
   | Tâche | Modèle | Pourquoi |
   |:-|:-|:-|
   | Extraction en masse (lire 200 fichiers, trier) | Haiku | rapide, peu cher, assez bon pour extraire |
   | Analyse, résumé, code mécanique déjà planifié | Sonnet | bon équilibre |
   | Décision difficile, débogage, code critique, texte dans la voix de la personne | le plus fort (Opus ou équivalent) | raisonnement profond |
   | Le plan et l'orchestration | le modèle de la session | il voit tout |
   Règle dure : un texte dans la voix de la personne ne part jamais sur Haiku. Le modèle de la session se règle avec `/model` ; celui d'un sous-agent avec `model:` dans son fichier, ou le paramètre `model` à l'appel.

3. **Le modèle par défaut des sous-agents (2 min).** Claude ajoute dans `~/.claude/settings.json`, clé `env` : `"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"`. La session garde le gros modèle pour planifier, les sous-agents travaillent sur Sonnet sauf indication.

4. **L'effort (3 min).** Si la version le propose (`/effort` ou `effortLevel` dans les réglages), Claude explique : effort bas pour les petites tâches, haut pour les décisions. Un modèle fort en effort bas bat souvent un modèle moyen en effort haut : à tester sur un vrai cas.

5. **Créer un agent (15 min).** Claude copie `outils/agent-modele.md` vers `.claude/agents/lecteur.md` et l'adapte (dossiers interdits de la personne). Pour un autre rôle, même structure : `name`, `description` (quand l'utiliser, comme un déclencheur), `tools` (le minimum : un agent qui ne doit rien écrire n'a ni Write ni Edit ni Bash), `model`, puis les consignes. Un agent qui touche à des données privées a une liste d'outils fermée.

6. **Bien briefer (5 min).** Claude ajoute à `wiki/maps/modeles.md` le gabarit de brief : le but, ce qui est déjà exclu, les fichiers où chercher, le format de retour, la limite (« lecture seule »). Un sous-agent ne sait que ce qu'on lui écrit.

7. **Tester le choix par la mesure (20 min, quand un doute coûte).** Pour un vrai doute (« Sonnet abîme-t-il ma voix ? »), Claude lance le même travail sur deux modèles avec `claude -p "<consigne>" --model <modèle> --output-format json` et compare côte à côte les sorties et le champ `total_cost_usd` (équivalent au tarif public, indicatif sur abonnement). La personne juge sur les sorties brutes. La décision va dans `wiki/maps/modeles.md`.

## Test
Claude pose une vraie question qui demande de parcourir un gros dossier du vault. Il la délègue à l'agent `lecteur` et reçoit une réponse de 3 lignes avec des chemins exacts. Le contexte de la session ne contient pas les fichiers lus (seulement la synthèse).

## Pièges vécus
- **Déléguer une petite chose.** Lancer un sous-agent pour modifier deux lignes coûte plus que de le faire : il relit tout depuis zéro. Seuil : moins de 3 fichiers, on le fait soi-même.
- **La voix sur le petit modèle.** Un texte de vente écrit sur le petit modèle a perdu la voix d'un coup. Règle dure dans la matrice.
- **Le sous-agent qui confirme l'hypothèse.** Un agent à qui on donne sa propre conclusion revient en la confirmant. Pour une relecture honnête, donne le travail, pas ton avis.
- **Les agents qui écrivent partout.** Un agent sans liste d'outils hérite de tout. Liste fermée pour chaque agent qui n'a pas besoin d'écrire.
- **Croire sans mesurer.** La peur « le moyen est moins bon » a été renversée par un test de 20 minutes. Teste avant de trancher.

## Entretien dans le temps
- À chaque nouvelle génération de modèles, Claude refait le test de l'étape 7 sur un cas réel et met à jour `wiki/maps/modeles.md`.
- Quand un sous-agent rend une synthèse fausse, Claude corrige son brief ou son fichier d'agent le jour même.

## Après
Coche la ligne `sous-agents-modeles` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, puis propose la brique suivante : creer-un-skill.
