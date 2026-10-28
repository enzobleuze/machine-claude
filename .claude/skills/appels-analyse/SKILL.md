---
name: appels-analyse
description: "Branche l'enregistrement des appels (Fathom ou autre), analyse chaque appel (résumé, verbatims, objections, moment de bascule, moments forts) et alimente trois banques : objections réelles, expériences vécues, mots du client. Utiliser quand l'utilisateur dit « analyse mon appel », « j'ai eu un appel avec X », « analyse tous mes appels », « quelles objections reviennent ». Pas pour la grille technique de vente (utiliser appel-de-vente, partie débrief)."
---
# Enregistrement et analyse des appels

## Pourquoi
Les appels contiennent la matière la plus précieuse d'un business de service : les mots exacts des clients, leurs vraies objections, les histoires qui touchent. Dans le système d'origine, plus d'une centaine d'appels dormaient dans un outil d'enregistrement. Une fois analysés en lot, ils ont donné un corpus d'objections comptées avec les réponses qui ont marché, et une banque d'expériences où les contenus vont piocher au lieu d'inventer des exemples.

## Prérequis
- `fiches-clients`.
- Si `ingestion-appels` (bloc A) est déjà fait, les transcriptions sont dans `raw/appels/` et la banque d'expérience existe : saute les étapes 1 et 5, et complète l'existant au lieu de le recréer.
- Un outil d'enregistrement avec transcription : Fathom, Granola, Zoom, Google Meet, ou un enregistreur local avec Whisper. Coût : souvent une offre gratuite suffit pour commencer.
- Optionnel : le connecteur MCP de l'outil (Fathom et Granola en ont un), sinon l'export des transcriptions.

## Interview
**Lis d'abord** : `wiki/appels/` s'il existe, `raw/` (cherche « transcript », « fathom », « call »), les fiches clients (section Appels), `wiki/business/offres.md`.

Puis demande :
1. Avec quoi enregistres-tu tes appels aujourd'hui ? Si rien : préfères-tu un outil en ligne ou un enregistrement sur ton ordinateur ?
2. Quels types d'appels fais-tu ? (Découverte, vente, séance client, suivi.)
3. As-tu l'accord de tes clients pour enregistrer ? (À demander en début d'appel ou dans le contrat.)
4. Combien d'anciens appels existent ? On les analyse en lot une fois, puis chaque nouveau au fil de l'eau.
5. Qu'est-ce que tu veux apprendre de tes appels en priorité ? (Pourquoi ils n'achètent pas, ce qui aide le plus, des histoires pour ton contenu.)

## Construire
1. **Brancher l'enregistreur (utilisateur guidé, 15 min).** Option A : installe l'outil choisi, connecte ton agenda, active « enregistrer automatiquement mes appels ». Option B : connecte son MCP dans Claude Code (`claude mcp add …` selon la page du connecteur) et Claude teste avec « liste mes 3 derniers appels ». Option C (hors ligne) : enregistre en local, dépose le fichier audio dans `raw/appels/`, Claude transcrit avec Whisper. Ajoute la phrase d'accord dans le script d'appel : « Je l'enregistre pour ne rien rater, ça te va ? »
2. **Gabarit d'analyse (Claude, 10 min).** Crée `wiki/appels/_gabarit.md` avec ces sections, dans cet ordre :
   - Résumé en 5 lignes (qui, situation, demande, issue, prochain pas).
   - Classification (type d'appel, issue : vendu, pas vendu, à relancer, absent).
   - Verbatims du client, mot pour mot, avec le minutage.
   - Objections, chacune avec sa forme exacte, la réponse donnée, et si ça a marché.
   - Moment de bascule : la phrase précise où l'appel a tourné, en bien ou en mal.
   - Moments forts : ce que l'utilisateur a dit de juste, à garder.
   - Ce qui va dans les banques (objections, expériences, mots).
3. **Analyser un appel (Claude, 15 min par appel).** Récupère la transcription. Remplis le gabarit dans `wiki/appels/<AAAA-MM-JJ>-<prenom>.md`. Chaque citation vient de la transcription, jamais reformulée. Ajoute une ligne au Journal de la fiche client et le lien dans sa section Appels.
4. **Les trois banques (Claude, 15 min).**
   - `wiki/business/objections.md` : une section par objection (« je dois réfléchir », « c'est trop cher », « je dois en parler à ma femme »…), avec les verbatims, le compte, et les réponses qui ont fermé ou non.
   - `wiki/maps/banque-experience.md` : des situations réelles par thème, résumées sans nom ni détail traçable. Les skills de contenu piochent ici, une expérience à la fois, sans réutiliser la même deux fois de suite.
   - `wiki/business/client-ideal.md`, section « Ses mots exacts » : ajoute les nouvelles phrases fortes.
5. **Lot des anciens appels (Claude en sous-agents, 20 min par lot de 10).** Lance un sous-agent par lot avec le gabarit. Chaque sous-agent rend seulement les fichiers d'analyse et les lignes pour les banques. Fusionne toi-même dans les banques pour éviter les doublons.
6. **Au fil de l'eau (Claude, 5 min).** Si l'outil a un MCP, ajoute au rapport du matin (bloc F) : « nouveaux appels non analysés : N ». L'utilisateur dit « analyse mon appel avec X » et Claude fait l'étape 3.

## Test
Un appel réel est analysé dans `wiki/appels/`, chaque citation se retrouve mot pour mot dans la transcription, et `objections.md` contient au moins une objection avec son verbatim et son issue.

## Pièges vécus
- **La citation inventée.** Un résumé qui « cite » le client avec des mots qu'il n'a pas dits ruine la confiance dans tout le corpus. Vérifie chaque guillemet dans la transcription.
- **Juger la personne au lieu du geste.** Une analyse qui accable l'utilisateur ne sert à rien. Nomme les gestes, garde toujours au moins une chose qui a marché.
- **La même histoire partout.** Sans rotation, le même exemple de client revenait dans plusieurs contenus. Note dans la banque la date de dernière utilisation.
- **Un appel de proche dans le lot.** Exclus les appels personnels et ceux sans accord d'enregistrement avant l'analyse.

## Entretien dans le temps
- Chaque appel de vente : analyse plus débrief (`appel-de-vente`).
- Une fois par mois : recompte des objections, et la réponse qui marche le mieux remonte dans le script d'appel.
- Une fois par trimestre : relecture de `wiki/maps/banque-experience.md` pour retirer ce qui pourrait identifier quelqu'un.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire si l'utilisateur a une préférence d'outil. Propose ensuite `repondre-client`.
