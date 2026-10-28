---
name: ingestion-reseaux
description: "Transforme les publications sauvegardées sur les réseaux (Instagram d'abord, aussi TikTok, X, LinkedIn) en techniques réutilisables : liste des saves depuis l'export officiel, regroupement par technique, playbooks, et propositions concrètes à valider. Utiliser quand l'utilisateur dit « mes saves Instagram », « j'enregistre plein de posts et je n'en fais rien », « point réseaux ». Pas pour publier ou écrire des posts (bloc E)."
---
# Ingestion des saves des réseaux

## Pourquoi
Dans le système d'origine, la personne sauvegardait des centaines de vidéos utiles (accroches, techniques de vente, astuces d'outils) sans jamais les revoir. Une première version rangeait chaque save dans le wiki, une page par post : le wiki s'est rempli de fiches que personne ne relisait, et ce moteur a fini par être abandonné. La version qui marche regroupe les saves par technique, en tire des playbooks, puis propose des changements concrets (un skill, une règle, une idée de contenu) que la personne valide. Une grosse part des saves est du bruit (humour, voyage) et doit être écartée vite.

## Prérequis
- architecture-vault, ingestion-fichiers.
- Python 3.9+.
- Pour lire les vidéos : `yt-dlp` et `ffmpeg` (gratuits) pour télécharger une vidéo publique, et une transcription locale (par ex. `faster-whisper`) ou les sous-titres fournis. Optionnel.

## Interview
Lis d'abord : `wiki/maps/architecture.md`, `wiki/maps/ingestion.md`, la liste des skills de `.claude/skills/`.

Puis demande :
1. « Sur quels réseaux tu sauvegardes des choses utiles ? »
2. « Tu ranges tes saves dans des collections ? Laquelle est pour le travail ? » Si non, propose d'en créer une (« Cerveau ») et de n'y mettre que le travail.
3. « Qu'est-ce que tu cherches surtout dans ces saves ? » (accroches, vente, outils, ton métier). Ce seront les familles de techniques.
4. « Tu préfères que je propose des changements une fois par semaine ou à la demande ? »

Range les réponses dans `wiki/maps/reseaux-saves.md` (réseaux, collection, familles, rythme), avec 3 liens.

## Construire
1. **Export officiel (10 min, ses mains, puis attente).** Instagram : Paramètres > Espace Comptes > Vos informations et autorisations > Télécharger vos informations > choisir « Certaines de vos informations » > cocher « Publications enregistrées » > format JSON > période. Le lien arrive par email, parfois après plusieurs heures. Dézippe dans `raw/reseaux/export-instagram-AAAA-MM-JJ/`. TikTok, X, LinkedIn ont un équivalent dans leurs réglages de confidentialité.
2. **Liste des saves (2 min).** Copie `outils/saves-export.py` vers `scripts/`, puis :
   ```bash
   python scripts/saves-export.py raw/reseaux/export-instagram-AAAA-MM-JJ --reseau instagram
   ```
   Sortie : `raw/reseaux/saves-instagram-AAAA-MM-JJ.md`, une ligne par save nouveau (date, auteur, lien). Les saves déjà vus sont ignorés grâce à `_vus.txt`.
3. **Tri rapide (15 min par lot de 30).** Pour chaque save : la légende, et si besoin la vidéo (sous-titres ou transcription locale). Verdict en trois piles : technique (on garde), idée de contenu, bruit (écarté avec un mot de raison). Écris le résultat dans `wiki/maps/reseaux-saves.md`, section « Tri du AAAA-MM-JJ ».
4. **Playbooks (15 min).** Les techniques qui se ressemblent fusionnent en un playbook : `wiki/principes/playbook-<technique>.md` (ce que c'est, quand l'utiliser, les étapes, 2 ou 3 exemples avec lien vers le save, ce qui peut rater). Jamais une page par save.
5. **Propositions (10 min).** Pour chaque playbook neuf, une proposition en 5 lignes : quoi changer (skill, règle, idée de contenu), où, pourquoi, comment le tester. Les skills proposés s'écrivent dans `outputs/skills-en-attente/<nom>/SKILL.md` et ne s'installent qu'après le oui de la personne sur le texte.
6. **Commande (3 min).** `.claude/commands/point-reseaux.md` qui enchaîne les étapes 2 à 5 sur le dernier export et finit par la liste des propositions.

## Test
Après un premier passage : `raw/reseaux/saves-*.md` existe, chaque save du lot a un verdict, au moins un playbook a été créé ou enrichi avec 3 liens, et la personne a dit oui ou non à chaque proposition. Relancer `saves-export.py` sur le même export affiche « Aucun save nouveau ».

## Pièges vécus
- Une page wiki par save : wiki gonflé, rien d'utilisé. On fusionne en playbooks.
- Lecture du compte par des cookies de navigateur et une API non officielle : marchait, puis cassait à chaque changement du réseau, et expose le compte à un blocage. L'export officiel est plus lent mais sûr. Si la personne choisit quand même l'automatisation par navigateur, c'est son compte et sa décision, à lui expliquer clairement.
- Copier les mots d'un créateur : on garde le mécanisme, jamais le texte.
- Skill installé par une tâche de nuit sans relecture : un skill change le comportement de Claude, il passe toujours par le oui de la personne.

## Entretien dans le temps
Un export par mois (ou au rythme choisi), puis le point réseaux. Quand une famille de techniques ne produit plus rien, retire-la des familles. Les playbooks utilisés souvent montent dans les cartes du bloc E.

## Après
Coche la ligne `ingestion-reseaux` dans `wiki/maps/parcours.md`, entrée dans `log.md`, ligne « point réseaux » dans `wiki/maps/routage.md`, puis propose la source suivante de son interview, ou le bloc B si toutes sont branchées.
