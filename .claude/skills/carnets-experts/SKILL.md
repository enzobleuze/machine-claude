---
name: carnets-experts
description: "Choisit, crée et remplit les carnets NotebookLM de l'utilisateur : un carnet par expert ou par domaine qui compte dans son métier, plus un carnet de sa propre méthode et, si utile, un carnet de la voix de ses clients. Tient le registre carnets.json. Utiliser quand l'utilisateur dit « quels carnets je crée ? », « ajoute un expert », « fais un carnet avec ces vidéos ». Pas pour brancher l'outil (utiliser notebooklm-brancher) ni pour décider quel carnet interroger (utiliser routage-carnets)."
---
# Les carnets d'experts

## Pourquoi
Claude seul imagine ce qu'un expert dirait, et il l'imagine avec assurance. Un carnet NotebookLM ne répond que depuis les sources qu'on y a mises, source citée à l'appui. Dans le système d'origine, chaque expert de référence a son carnet, la méthode du fondateur a le sien (les transcriptions de son programme), et les paroles de ses clients (pseudonymisées) un autre. Le comité et le board des textes s'appuient sur eux : un siège égale un carnet.

## Prérequis
- `notebooklm-brancher` fait (auth OK, `scripts/nlm_ask.py` en place).
- Les sources : vidéos YouTube, PDF, livres que l'utilisateur possède, transcriptions de ses propres formations ou appels.
- Coût : zéro hors offre Google. La limite de sources par carnet dépend de l'offre du PROPRIÉTAIRE du carnet.

## Interview
Lis d'abord : `wiki/maps/` (une carte du métier ou du client idéal existe peut-être, bloc D), `wiki/sources/` (les auteurs déjà cités), `notebooklm list` (les carnets existants), `carnets.json` s'il existe.

Puis demande, en petit lot :
1. « Quels sont les deux à cinq experts, auteurs ou écoles dont tu suis la pensée dans ton métier ? » Exemples à donner : pour un coach, les auteurs qu'il cite ; pour une boulangère, les livres de technique et un ou deux artisans qu'elle admire ; pour un consultant, les penseurs de son domaine et un expert vente.
2. « Sur le fond de ton métier, lequel fait foi quand ils se contredisent ? » (un seul ; c'est lui qui tranche au board).
3. « As-tu ta propre méthode enregistrée quelque part (formation, vidéos, notes de cours, appels) ? » (devient le carnet `methode`).
4. « As-tu des paroles écrites ou enregistrées de tes clients (messages, questionnaires, appels) ? » (devient le carnet `voix-client`, seulement pseudonymisé).
5. « Pour vendre et te faire connaître, qui t'inspire (offre, écriture, réseaux sociaux) ? » (carnets de rôle `performance`).
6. « Quelles sources as-tu déjà sous la main pour chacun : liens de chaînes, PDF, livres ? »

Range les réponses dans `carnets.json` (gabarit `outils/carnets.modele.json`) et une fiche courte par auteur dans `wiki/sources/auteur-<nom>.md` (qui il est, ce qu'il couvre, ce qu'il ne couvre pas). Ces fiches servent aussi au contrôle des attributions (skill `controle-verite`).

## Construire
1. **Faire la liste** (Claude, 10 minutes). Propose une table : carnet, rôle (`fond`, `methode`, `performance`, `voix-client`), auteur, sources prévues. Règle : un auteur par carnet. Mélanger deux auteurs dans un carnet brouille le garde-fou et les citations. Valide la table avec l'utilisateur.
2. **Créer chaque carnet** (Claude) : `notebooklm create "<titre>" --json`, noter l'identifiant rendu dans `carnets.json` (`id`).
3. **Ajouter les sources** (Claude), par lots :
   - Liens (YouTube, pages) : `notebooklm source add-async -n <id> <url1> <url2> ...` par lots de 20, puis `notebooklm source list -n <id>` jusqu'à ce qu'elles soient prêtes.
   - Fichiers : `notebooklm source add -n <id> <fichier.pdf>`.
   - Une chaîne YouTube entière : Claude liste les vidéos (par exemple avec `yt-dlp --flat-playlist --print url <lien de la chaîne>`), garde les plus utiles au métier, puis ajoute par lots.
   - Livres : seulement ceux que l'utilisateur possède légalement, en fichier.
4. **Carnet de la méthode** (si la question 3 a donné quelque chose). Transcrire les vidéos ou audios du programme (skill d'ingestion du bloc A), une source par module ou leçon, titre clair (« Module 2, leçon 3 : ... »). Ce carnet est INTERNE : son contenu n'apparaît jamais tel quel dans un texte public (`"public": "interne"`).
5. **Carnet voix-client** (si la question 4 a donné quelque chose). D'abord pseudonymiser avec `controle-verite` (`verite.py pseudonymiser`), vérifier zéro nom (`verite.py noms`), seulement ensuite envoyer chez Google. Les vrais noms et la table de correspondance restent sur la machine, dans `.gitignore`.
6. **Test d'identité de chaque carnet** (Claude). Une question par carnet, dans un fichier, amorce comprise : « Réponds UNIQUEMENT depuis les sources de ce carnet et cite la source de chaque point. Quels sont les trois principes que ces sources répètent le plus, avec une phrase citée mot pour mot pour chacun ? » Lancer `python scripts/nlm_ask.py ask <clé> <fichier>`. Montrer la réponse à l'utilisateur : « Est-ce bien la pensée de cet auteur ? »
7. **Mettre à jour** `carnets.json` (nombre de sources, date) et la page `wiki/maps/carnets.md` : une ligne par carnet (clé, rôle, auteur, ce qu'il juge, ce qu'il ne juge pas).

## Test
Chaque carnet de `carnets.json` a un identifiant réel, et sa question d'identité (étape 6) sort 0 avec au moins une source citée. L'utilisateur a reconnu la pensée de chaque auteur.

## Pièges vécus
- **Un carnet « audit business » répond toujours pareil.** Un carnet d'expert en offres répondait « arrête la technique, va vendre » à toute question vague. Il sert pour les priorités, l'offre, le prix ; pas pour le détail de l'écriture. Un carnet dédié à l'écriture de vente a mieux répondu sur l'écriture. Note dans `wiki/maps/carnets.md` ce que chaque carnet juge bien.
- **La limite de sources est celle du propriétaire du carnet.** Un compte invité qui interroge un carnet partagé profite des sources du propriétaire, mais garde sa propre limite de questions.
- **Langue.** Les carnets d'auteurs anglophones répondent mieux en anglais. Le carnet de la méthode, s'il est en français, s'interroge en français, sans traduction.
- **Contenu payant.** Les transcriptions d'une formation vendue restent internes. Jamais dans un texte public, jamais en pièce jointe.
- **Paroles de clients.** Rien ne part chez Google avant le contrôle anti-noms. Un prénom rare mal transcrit peut échapper au masquage : ajouter les variantes à la liste privée.
- **Ajout par lots.** Des dizaines de vidéos YouTube passent « prêtes » en quelques minutes quand on les envoie par lots de 20 avec `add-async`. Une à une, c'est long et fragile.

## Entretien dans le temps
- Quand l'utilisateur dit « ajoute cet expert » ou colle une chaîne : refaire les étapes 2, 3, 6 et 7 pour ce carnet.
- Une fois par trimestre : proposer d'ajouter les nouvelles vidéos des auteurs suivis (même méthode par lots), et retirer les sources qui n'ont jamais servi.
- Le carnet de la méthode se complète à chaque nouveau module enregistré.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la note mémoire `reference_notebooklm.md` (liste des clés de carnets, jamais leurs identifiants dans un texte public). Propose ensuite `routage-carnets`.
