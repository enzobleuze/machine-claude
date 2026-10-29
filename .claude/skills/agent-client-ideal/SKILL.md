---
name: agent-client-ideal
description: "Construit le sous-agent client-ideal : un client composite, nourri des vraies paroles pseudonymisées des clients de l'utilisateur, avec 3 à 5 personas, qui lit un texte et dit où il décroche, ce qui le touche, ses mots à lui, son objection et s'il agirait (mode test), ou répond comme un client qu'on interroge (mode conversation). Utiliser quand l'utilisateur dit « fais-moi un client à qui tester mes textes », « est-ce que mon client comprendrait ça ? », « interroge mon client idéal ». Pas pour définir le client idéal la première fois (utiliser l'entretien fondateur du bloc D)."
---
# L'agent client idéal

## Pourquoi
Les mots exacts des clients battent tout ce que Claude imagine. Dans le système d'origine, on a fabriqué un client que Claude peut jouer, nourri des vraies paroles des clients (appels, messages, questionnaires), pseudonymisées. Chaque contenu passe devant lui avant d'arriver chez le fondateur. Il est devenu un siège obligatoire du board des textes, et ses « phrases fortes » nourrissent la banque d'accroches.

## Prérequis
- La fiche du client idéal (entretien fondateur, bloc D) et des paroles réelles de clients : messages, emails, questionnaires, transcriptions d'appels (bloc A, ingestion).
- `controle-verite` (pour pseudonymiser). Fais-le avant si besoin.
- Conseillé : `dossier-client-ideal` (bloc D). Ses situations deviennent les personas, et ses pensées secrètes, fausses croyances et objections remplissent les crochets de l'agent.
- Facultatif : un carnet `voix-client` (skill `carnets-experts`) pour retrouver des phrases exactes par thème.
- Coût : un sous-agent Sonnet par passage.

## Interview
Lis d'abord : la fiche client idéal du vault, `wiki/clients/` (pour compter les cas, jamais pour copier un nom), les transcriptions d'appels et messages déjà ingérés, les questionnaires.

Puis demande :
1. « Où sont les paroles de tes clients, écrites ou enregistrées ? Donne-moi les dossiers ou les exports. » (messagerie, CRM, formulaires, appels.)
2. « Quelles sont les trois à cinq situations dans lesquelles tes clients arrivent chez toi ? » (chaque situation devient une persona.)
3. « Lequel de tes clients est le plus méfiant, le plus dur à convaincre ? » (devient la persona de contrôle.)
4. « Quels mots tes clients ne disent JAMAIS, alors que toi tu les dis ? » (le jargon à bannir du rôle.)
5. « Qui doit passer devant lui : tous les textes, ou certains seulement ? » (proposer : tous ceux qui parlent aux clients.)

Range : les personas dans `.claude/agents/client-ideal.md`, la liste des sources dans `wiki/business/client-ideal.md`, la règle « tout texte client passe devant lui » dans `CLAUDE.md`.

## Construire
1. **Rassembler les paroles** (Claude). Lister les fichiers de paroles réelles. Écrire la liste privée des noms à masquer `outputs/client-ideal/noms-prives.txt` (vrais prénoms et noms des clients, de leurs proches, des personnes citées), et l'ajouter au `.gitignore` avec `outputs/client-ideal/table.json` et `outputs/client-ideal/sources/`.
2. **Pseudonymiser** (Claude), fichier par fichier :
   ```
   python scripts/verite.py pseudonymiser <fichier> outputs/client-ideal/sources/<paquet>.md --liste outputs/client-ideal/noms-prives.txt --table outputs/client-ideal/table.json
   ```
   Le script remplace chaque nom par « Client 001 », toujours le même pour la même personne, masque emails et téléphones, puis vérifie qu'aucun nom ne reste (sortie 0). Sortie 1 : compléter la liste et relancer.
3. **Extraire les verbatims** (Claude) dans `outputs/client-ideal/verbatims.md` : les phrases exactes des clients, classées par situation (une section par persona, plus « ce qui les retient », « ce qu'ils ont déjà essayé », « ce qu'ils veulent vraiment »). Mot pour mot, jamais reformulées. Relancer `verite.py noms` sur ce fichier : sortie 0 obligatoire.
4. **Écrire l'agent** (Claude). Copier `.claude/agents/client-ideal.modele.md` du repo vers `.claude/agents/client-ideal.md` du vault et remplir chaque crochet avec ce que disent les verbatims et l'interview : la scène où il tombe sur le texte, ses mots, sa fausse croyance, ses personas (des composites, aucune n'est un vrai client). Garder la liste des dossiers interdits de lecture.
5. **Montrer les personas** à l'utilisateur : « Tu reconnais tes clients ? Qu'est-ce qui sonne faux ? » Corriger.
6. **Brancher** (Claude) : dans chaque skill qui écrit pour les clients, une étape « Client idéal » avant de montrer le texte : sous-agent `client-ideal`, mode test, persona visée plus persona de contrôle. Seuil : bloquant sous 6 sur 10 chez la persona visée, ou si elle se sent jugée ou honteuse. Le board des textes l'appelle aussi.
7. **Facultatif, en automatique** (tâches de nuit, bloc F) : le même rôle peut tourner en `claude -p --model sonnet` sans outils, avec le corps de l'agent comme prompt système et le texte en entrée. Une régénération si la note est sous le seuil, sinon le texte part en « à relire », jamais bloqué en silence.
8. **Compter** : une ligne par passage dans `outputs/client-ideal/usage.jsonl` (date, texte, persona, note). Ça montre s'il sert vraiment.

## Test
Deux preuves, les deux obligatoires :
- `python scripts/verite.py noms outputs/client-ideal/verbatims.md --liste outputs/client-ideal/noms-prives.txt` sort 0.
- Sur un texte réel, l'agent en mode test rend le format complet pour une persona, avec au moins une ligne exacte citée du texte et au moins une expression tirée des verbatims dans « Mes mots à la place ». L'utilisateur juge la réaction crédible.

## Pièges vécus
- **Seuls les paquets pseudonymisés quittent la machine.** Le carnet voix-client chez Google ne reçoit que des fichiers passés au contrôle anti-noms. Les vrais noms et la table restent locaux.
- **Un prénom rare mal transcrit échappe au masquage.** Le contrôle couvre la liste, pas toutes les fautes de transcription. Relire une fois les paquets à la main, ajouter les variantes.
- **La note varie d'un ou deux points d'un appel à l'autre** sur le même texte. Une note juste sous le seuil sans ligne fautive nommée se rejoue une fois.
- **Le seuil trop haut bloque tout.** Sur des centaines de passages, la médiane était pile au seuil : « égal ou moins » aurait bloqué presque tous les textes. Bloquer strictement sous le seuil.
- **Sa réaction reste une hypothèse.** Les vrais chiffres (lecture, réponses, rendez-vous) tranchent. Il sert à éviter les textes qui ratent, il ne remplace pas la mesure.
- **Pas pour répondre à un vrai client.** Quand on répond à un client dont on a la fiche, l'avatar n'ajoute rien : la fiche réelle compte.

## Entretien dans le temps
- Chaque mois, les nouvelles paroles de clients (appels, messages) passent par les étapes 2 et 3 : les verbatims grossissent, l'agent s'affine.
- Une fois par trimestre : comparer ses notes aux résultats réels des textes publiés. Si un texte noté bas a bien marché (ou l'inverse), revoir la persona concernée.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (« tout texte client passe devant l'agent client-ideal »). Propose ensuite `board-textes` s'il n'est pas fait.
