---
name: board-textes
description: "Installe le board des textes : tout texte destiné aux clients de l'utilisateur (post, email, page, script vidéo, carrousel, message, prompt d'un agent) passe devant des sièges (ses carnets d'experts, sa méthode, le vault, le client idéal, la voix, la vérité), affirmation par affirmation, en 2 tours au plus, avec un board.md et une porte par empreinte qui refuse tout texte modifié après le verdict. Utiliser quand l'utilisateur dit « valide ce texte », « passe-le au board », « est-ce que je peux publier ça ? », ou avant toute publication ou tout envoi. Pas pour une décision à options (utiliser comite-roast-ancre), pas pour une idée sans texte rédigé, pas pour de la logistique pure."
---
# Le board des textes et sa porte

## Pourquoi
Un texte relu « en gros » passe avec ses failles. Dans le système d'origine, un carnet d'expert interrogé par « OK ou correction ? » a déclaré une copie entièrement alignée ; le même jour, le même carnet, interrogé affirmation par affirmation, a cassé une phrase d'exemple que le client devait envoyer telle quelle. Depuis, une règle que rien ne contourne : tout texte qui parle au client idéal passe au board avant d'être publié ou envoyé, et une commande (la porte) refuse de s'ouvrir si le texte a bougé d'une virgule depuis le verdict.

## Prérequis
- `notebooklm-brancher`, `carnets-experts`, `routage-carnets` faits.
- `agent-client-ideal`, `controle-verite`, `controle-voix` faits (ce sont des sièges du board ; on peut installer le board avant et les ajouter ensuite, la porte les exigera dès qu'ils sont dans `board-config.json`).
- La recherche par le sens du bloc A (`recherche-par-le-sens`, `scripts/cerveau.py`) : c'est le siège Bibliothécaire.
- Python 3.8 ou plus. Coût : quelques questions aux carnets par texte (voir Pièges).

## Interview
Lis d'abord : `carnets.json` (rôles `fond`, `methode`, `performance`), `wiki/maps/routage-carnets.md`, le guide de voix (bloc D), `regles-voix.json`, la fiche du client idéal, et les textes que l'utilisateur publie (bloc E).

Puis demande, en petit lot :
1. « Quels textes envoies-tu ou publies-tu pour tes clients ? » (la liste des types : post, email, page, script, carrousel, message privé, prompt d'agent, devis.)
2. « Sur le fond, quel expert fait foi ? Et ta propre méthode, elle a un carnet ? » (les sièges toujours joués.)
3. « Quels experts n'ont leur mot à dire que sur certains textes ? » (exemple : l'expert vente seulement quand le texte vend, l'expert réseaux seulement quand il se publie sur un réseau.)
4. « Quand ton expert de fond et ta méthode se contredisent, qui tranche ? » (réponse attendue : l'utilisateur ; ses choix se notent dans `wiki/maps/doctrine-arbitrages.md`.)
5. « Quels textes sont exemptés ? » (proposer : logistique pure, comme un horaire, un lien, une facture.)
6. « Tes réponses à des clients réels : board complet, ou version légère ? » (proposer la version légère.)

Range : la liste des sièges et leurs types dans `wiki/maps/board-textes.md`, les sièges requis dans `board-config.json` (gabarit `outils/board-config.modele.json`), la règle dans `CLAUDE.md`.

## Construire
1. **Poser la porte** (Claude, 5 minutes). Copier `outils/porte_board.py` dans `scripts/porte_board.py` du vault, `outils/board-config.modele.json` en `board-config.json` à la racine (avec les vrais noms de sièges), `outils/board.modele.md` en `wiki/maps/board-modele.md`. Puis `python scripts/porte_board.py selftest` doit imprimer `selftest OK`.
2. **Écrire la table des sièges** (Claude) dans `wiki/maps/board-textes.md` :
   | Siège | Il juge | Outil | Types |
   |:-|:-|:-|:-|
   | Expert fond | le fond est vrai et utile (fait foi) | carnet `fond`, gabarit AFFIRMATIONS | tous |
   | Méthode | le texte dit ce que la méthode de l'utilisateur dit, avec ses mots | carnet `methode` | tous |
   | Bibliothécaire | une scène vécue et un principe du vault portent le texte ; aucun conseil ne contredit une page | `python scripts/cerveau.py "<sujet>"` avec 2 ou 3 reformulations, sauvé dans `bibliothecaire.md` | tous |
   | Client idéal | il se reconnaît, lit jusqu'au bout, agit | agent `client-ideal`, mode test | tous |
   | Expert second | son champ seulement (exemple : un spécialiste du conflit) | son carnet | quand le texte touche son champ, sinon « sans objet » |
   | Performance | une seule action claire, promesse pas plus grande que la preuve, accroche | carnets `performance`, gabarit RELECTURE | quand le texte vend ou se publie |
   | Voix | règles dures mesurables | `lint_voix.py` (skill `controle-voix`) | tous |
   | Vérité | chiffres, attributions, noms de clients | `verite.py` (skill `controle-verite`) | tous |
3. **Écrire le skill de séance** (Claude) dans `.claude/skills/board/SKILL.md` du vault, avec ce protocole :
   - **Préparer, gratuit d'abord.** Dossier de travail `W = <dossier du texte>/board-travail/`. Copie de l'original en `<nom>.avant-board.<ext>`. `python scripts/porte_board.py extraire <texte> W/texte.txt`. Lancer Voix et Vérité tout de suite : une violation se corrige avant de dépenser une seule question aux carnets.
   - **Numéroter les affirmations** dans `W/affirmations.txt`, 12 au plus : chaque conseil, chaque phrase sur les clients, **chaque phrase exacte que le client doit dire ou envoyer, mot pour mot**, la morale, l'action finale. Au-delà de 12, garder les plus risquées (catégoriques, phrases à envoyer, promesses de résultat).
   - **Tour 1, tout en parallèle dans un seul message** : une question par siège carnet (`W/ancrage-<siege>.txt`, puis `python scripts/nlm_ask.py ask <carnet> W/ancrage-<siege>.txt --sortie W`), l'agent client idéal (persona visée et une persona de contrôle, la plus méfiante), le Bibliothécaire, Voix, Vérité.
   - **Gabarit d'un siège de fond** (anglais si le carnet est anglophone, chaque phrase citée en version originale avec sa traduction) :
     ```
     Réponds UNIQUEMENT depuis les sources de ce carnet et cite la source de chaque point ; si tes sources ne disent rien sur un point, écris AUCUNE SOURCE.
     Tu vérifies un [type] pour [client idéal en une ligne]. Sujet : « [sujet] ». Compare chaque point numéroté à tes sources. Pour CHAQUE point : D'ACCORD, NUANCE ou PAS D'ACCORD, une phrase pourquoi, la source. Puis la correction la plus importante, et ce qui manque d'important pour cette situation.
     1. « [affirmation exacte] »
     ```
   - **Fusionner.** Chaque siège devient OK ou CORRECTION (avant, après, source). Bloquant : PAS D'ACCORD d'un siège de fond ou de la méthode ; leur NUANCE sur une phrase que le client dira ou un conseil qu'il appliquera ; le Bibliothécaire qui ne trouve aucune scène ni aucun principe (texte générique) ou trouve une page contraire ; le client idéal qui décroche avant la fin de l'accroche, se sent jugé, ou note sous le seuil ; toute règle dure de Voix ou de Vérité. Pas bloquant (noté) : les mots que le client propose (pris s'ils sont simples), l'objection de prix, ce qu'un expert juge « manquant ». Un siège appuyé sur une seule source ne bloque que si un autre dit la même chose.
   - **Ordre de contradiction.** Sur le fond, l'expert qui fait foi l'emporte ; la méthode de l'utilisateur donne en plus ses étapes et ses mots. Quand les deux divergent sur un point qui compte, le texte ne bouge pas : les deux avis, leurs sources et une recommandation vont à l'utilisateur. Il tranche ; son choix s'écrit dans `wiki/maps/doctrine-arbitrages.md` et tranche d'avance la prochaine fois. Pour le reste : vérité et sécurité du client d'abord, puis décisions écrites de l'utilisateur et règles de voix, puis client idéal, puis performance.
   - **Corriger en une passe**, relancer Voix à chaque modification (gratuit).
   - **Tour 2, le dernier** : seulement les sièges qui avaient bloqué, seulement sur les points NUANCE ou PAS D'ACCORD et les phrases réécrites. Une objection qui reste, ou deux sièges qui se contredisent encore : s'arrêter, verdict À TRANCHER, le désaccord va à l'utilisateur. Jamais de tour 3. Une phrase écrite après le tour 2 est marquée « non revue » et le verdict reste À TRANCHER.
   - **Sortie** : `board.md` à côté du texte (gabarit `wiki/maps/board-modele.md`), avec `Empreinte du texte final :` (sortie de `python scripts/porte_board.py empreinte <texte>`), `Sièges joués :`, et le titre `## Verdict : ...`. VERT demande : tous les sièges requis joués, zéro objection bloquante, aucune phrase « non revue », Voix propre sur le texte final.
4. **Brancher la porte** (Claude). Dans `CLAUDE.md` et dans chaque skill qui publie ou envoie (bloc E, bloc F) : « Avant de publier, d'envoyer ou de payer une image : `python scripts/porte_board.py verifier <texte> <board.md>` doit sortir 0. Toute retouche après le verdict relance le board sur les phrases changées. » Codes : 0 la porte s'ouvre ; 1 texte modifié ou verdict pas VERT ; 2 `board.md` illisible ; 3 siège requis manquant.
5. **Mode léger** (réponse à un client réel, rédigée en séance) : Bibliothécaire, expert de fond, client idéal (une persona), et la méthode si la réponse donne une marche à suivre. Ni `board.md` ni empreinte : l'utilisateur envoie lui-même. Le verdict se donne dans le chat.
6. **Exemptions** : logistique pure (horaire, lien, facture, accès). Dès qu'une phrase conseille, rassure ou promet, le texte repasse sous la règle.
7. **Tâche de nuit** (si le bloc F est en place) : le board peut tourner en automatique sur une file de textes, mêmes sièges, même porte. Un désaccord ou une question pour l'utilisateur ne se tranche jamais la nuit : verdict À TRANCHER, question rangée pour le matin. Si NotebookLM refuse, la tâche s'arrête et reprend la nuit suivante. Seul un texte VERT (empreinte identique) part ; les autres restent en brouillon « board non passé ».

## Test
Sur un vrai texte de l'utilisateur : une séance complète écrit `board.md` avec VERT, et `porte_board.py verifier` sort 0. Puis Claude ajoute un mot au texte et relance : la porte sort 1. Les deux, sinon la porte n'est pas branchée.

## Pièges vécus
- **« OK ou correction ? » rate les failles.** Seul le format affirmation par affirmation les trouve. Et c'est la phrase d'exemple, celle que le client doit dire mot pour mot, qui casse le plus souvent : elle a l'air anodine.
- **Question trop longue.** Au-delà d'environ 4 000 signes, NotebookLM refuse. Découper en lots de 4 à 6 affirmations, un fichier par lot, même amorce. Un long questionnaire a été refusé en entier, puis est passé en dix lots.
- **Réponse « les sources ne contiennent pas ».** Le plus souvent la question était trop large, pas le carnet faux. Resserrer, une reprise par siège et par tour.
- **Les carnets varient d'une fois à l'autre.** Au tour 2, une NUANCE sur un point jugé D'ACCORD au tour 1 et dont le texte n'a pas changé est notée, pas bloquante. Sinon le board tourne sans fin.
- **Un juge automatique varie aussi.** Une lecture hostile par un modèle a donné 4 réussites sur 4, puis 3 sur 4, sur un texte presque identique. Pour un juge de ce genre : trois passages et la majorité.
- **Le seuil du client idéal.** Sur des centaines de passages, la note médiane était juste au seuil choisi au départ : le seuil « égal ou moins » bloquait presque tout. Bloquer strictement sous le seuil, et rejouer une fois une note basse sans ligne fautive nommée.
- **Cohérence avec l'existant.** Une phrase conseillée dans un nouveau texte était déconseillée dans un texte déjà prêt. Chercher chaque phrase à dire dans le vault (`Grep`) avant le verdict ; une contradiction va à l'utilisateur avec les deux extraits.
- **Correction qui change la forme.** Ajouter ou couper un élément d'un carrousel casse sa mise en page. Une correction garde le même nombre d'éléments ; sinon c'est une décision de l'utilisateur.
- **`board.md` est interne.** Il cite les experts et la méthode : jamais dans un dossier de publication ni en pièce jointe.
- **Fichier tenu par un autre outil.** Ne pas l'écraser : écrire le texte corrigé dans `<nom>-board.<ext>`, c'est lui qui porte l'empreinte.

## Entretien dans le temps
- Chaque arbitrage de l'utilisateur va dans `wiki/maps/doctrine-arbitrages.md` ; les conseils écartés deviennent des motifs interdits ou des vérifications du contrôle de vérité.
- Une fois par mois : compter les textes publiés sans `board.md` VERT (il doit y en avoir zéro), et les sièges qui bloquent le plus. Un siège qui bloque souvent pour rien a une question mal posée : la reprendre.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, et la mémoire (la règle du board, en une ligne dans l'index). Propose ensuite `agent-client-ideal` s'il manque, sinon `skills-marketing`.
