---
name: dossier-client-ideal
description: "Construit le dossier du client idéal, mot à mot et sourcé : ses douleurs, ses peurs, ses désirs classés, ses rêves, ce qu'il a déjà essayé, les mythes et les fausses solutions de son domaine, ses objections, son déclic, ses pensées secrètes et ce qu'il fait en cachette, plus la bibliothèque de micro-moments à 3 niveaux de précision. C'est la matière de tout contenu. Utiliser quand l'utilisateur dit « approfondis mon client idéal », « qu'est-ce que mes clients ressentent vraiment ? », « fais le dossier client », « mon contenu ne touche personne ». Pas pour la première description rapide du client (utiliser entretien-fondateur), ni pour jouer le client sur un texte (utiliser agent-client-ideal)."
---
# Le dossier du client idéal

## Pourquoi
Dans le système d'origine, la phrase que les clients répétaient en appel était « comment tu sais exactement ce que je vis ? ». Elle venait de ce dossier : des centaines de phrases exactes de clients, classées par situation, et une bibliothèque de micro-moments vécus. Le contenu écrit avec des mots généraux (« tu te sens seule », « tu es épuisé ») ne touchait personne, même quand le fond était juste. Le contenu qui ouvrait sur une scène précise, avec la pensée que la personne n'avoue à personne, faisait commenter, écrire et réserver. Ce dossier est la matière première de tout le bloc E.

## Prérequis
- `entretien-fondateur` fait (au moins la séance 2 : la fiche `wiki/business/client-ideal.md` existe).
- Bloc A : ingestion des appels et des messages, recherche par le sens (`scripts/cerveau.py`).
- Conseillé (bloc C) : `controle-verite` pour pseudonymiser, un carnet `voix-client` et le carnet de l'expert qui fait foi (`carnets-experts`). Sans eux, le dossier se construit quand même depuis le vault, plus lentement.
- Aucun coût.
- Outils joints dans `outils/` : trois gabarits, un exemple rempli, les questions pour les carnets, `verifier-dossier.py`.

## Interview
**Lis d'abord** : `wiki/business/client-ideal.md`, `wiki/business/fondateur.md`, `outputs/client-ideal/verbatims.md` s'il existe, `carnets.json`, et cherche par le sens dans `raw/` et `wiki/` avec 2 ou 3 reformulations (« j'ai peur », « je n'en peux plus », « j'ai tout essayé », « ce qui m'a décidé »). Compte ce que tu as déjà : une phrase sourcée trouvée ne se redemande pas.

Puis demande, une question à la fois :
1. « Où sont les paroles de tes clients ? » Messages, emails, notes ou enregistrements d'appels, formulaires, commentaires, avis. Demande les dossiers ou les exports, et range-les dans `raw/paroles-clients/`.
2. « Combien de clients ou de prospects as-tu déjà eus en conversation, à peu près ? » Peu (moins d'une dizaine) : le dossier se complète par les sources publiques (étape 2) et par des récits de scène (question 3).
3. « Raconte-moi la dernière personne que tu as aidée, le soir où elle t'a écrit. Où était-elle ? Qu'avait-elle fait juste avant ? Qu'a-t-elle dit en premier ? » Copie la réponse mot à mot. Repose la question pour deux ou trois autres personnes.
4. « Quelles sont les 3 à 5 situations dans lesquelles les gens arrivent chez toi ? » Chacune aura son fichier de pensées.
5. « Sur le fond de ton métier, quel expert ou quelle école fait foi ? » (sert à trancher les mythes ; souvent déjà dans `carnets.json`).
6. « Quels mots de ton métier tes clients ne disent jamais ? » Ils vont dans les mots à bannir.

Range : les sources dans `raw/paroles-clients/`, les récits de l'utilisateur dans `raw/paroles-clients/recits-<date>.md`, les situations en tête de `wiki/business/client-ideal.md`.

## Construire
1. **Préparer (Claude, 10 min).** Copie les gabarits : `outils/gabarit-fiche.md` dans `wiki/business/client-ideal.md` (garde tout ce que l'entretien fondateur y a déjà écrit, range-le dans les bonnes sections), `outils/gabarit-precision.md` dans `wiki/business/precision-emotionnelle.md`, et `outils/gabarit-pensees.md` une fois par situation dans `wiki/business/pensees-client/<situation>.md`. Montre `outils/exemple-rempli.md` à l'utilisateur : « Voilà le niveau de précision qu'on vise. » L'exemple est inventé et d'un autre métier : rien ne s'en recopie.
2. **Rassembler les paroles (Claude, 20 min par lot).** Lis les sources de `raw/paroles-clients/` et du vault. Avec peu de clients, ajoute des sources publiques, toujours avec le lien : les commentaires sous les vidéos des créateurs du domaine, les questions posées sur les forums et groupes publics, et les avis de lecteurs sur les livres du domaine (cette dernière piste n'a pas été testée dans le système d'origine). Une source publique se marque `(public : <lien>)` ; elle ne remplace jamais les paroles des vrais clients, elle les complète.
3. **Extraire mot à mot (Claude, 20 min par lot).** Pour chaque phrase forte, une ligne dans la bonne section de la fiche, au format `- « <phrase exacte> » (<chemin ou lien de la source>)`. Nettoie seulement les « euh » ; coupe avec [...] quand la phrase déborde. Jamais de reformulation, jamais de prénom dans la phrase (remplace par [prénom]). Deux phrases qui disent la même chose fusionnent et leur compteur monte : c'est ce qui classe les désirs par fréquence.
4. **Interroger les carnets (Claude, 15 min).** Si un carnet `voix-client` existe, lance les questions de `outils/questions-carnet.md` (une catégorie par fichier, avec l'amorce) : `python scripts/nlm_ask.py ask voix-client <fichier>`. Chaque phrase rendue garde la source citée par le carnet. Puis soumets la liste des mythes et des fausses solutions au carnet de l'expert qui fait foi : un mythe n'est déclaré faux qu'avec sa source dans la ligne « Vrai : ».
5. **Écrire les sections de synthèse (Claude, 20 min).** Dans la fiche : le paradoxe central, le récit (héros, vrai ennemi, guide, fin heureuse), les profils, le tableau « ce qui déclenche l'achat », les 5 pourquoi, le questionnaire avant l'appel. Chaque affirmation pointe vers les phrases qui la prouvent. Le vrai ennemi n'est jamais le client lui-même : c'est ce qu'on lui a appris ou ce qu'il subit.
6. **La précision émotionnelle (Claude, 20 min).** Remplis `precision-emotionnelle.md` : pour chaque situation, une phrase au niveau 1, la même au niveau 2, la même au niveau 3. Puis la bibliothèque de micro-moments : chaque moment vient d'une phrase réelle et garde sa source. Un micro-moment inventé se voit : il est trop propre.
7. **Les pensées par situation (Claude, 20 min par fichier).** Remplis les 6 sections de chaque `pensees-client/<situation>.md`, en commençant par la situation la plus fréquente. La section 6 nomme honnêtement ce qui manque.
8. **Vérifier (Claude, 5 min).** `python scripts/verifier-dossier.py .` (copie l'outil dans `scripts/` du vault). Il contrôle les 12 sections, le nombre d'entrées, la source de chaque citation, les « Vrai : » des mythes, les gabarits non remplis et les tirets longs. Corrige jusqu'à la sortie 0.
9. **Faire reconnaître (avec l'utilisateur, 15 min).** Lis-lui les 5 pensées les plus fortes de la première situation et le micro-moment de niveau 3 : « Tu reconnais tes clients ? Qu'est-ce qui sonne faux ? » Corrige.
10. **Brancher (Claude, 10 min).** Vérifie que le `CLAUDE.md` du vault contient la section « Écrire pour son client » (voir `CLAUDE.modele.md` du kit) ; sinon ajoute-la. Ajoute la ligne de routage. Si `agent-client-ideal` est fait, propose de reconstruire ses personas depuis le dossier.

## Test
Deux preuves, les deux obligatoires :
- `python scripts/verifier-dossier.py .` sort 0 (au moins 3 entrées sourcées dans chacune des 12 sections, une bibliothèque de micro-moments, un fichier de pensées complet par situation).
- L'utilisateur lit le micro-moment de niveau 3 de sa situation principale et dit : « C'est exactement ce que mes clients vivent. »

## Pièges vécus
- **Claude reformule sans le vouloir.** « Il se sent seul » au lieu de « je suis tout seul contre le monde ». La phrase brute touche ; la reformulation ne touche personne. La règle est simple : guillemets, mot à mot, source.
- **Le niveau 1 se glisse partout.** Les mots généraux (froid, épuisé, perdu) sont vrais et ne font rien ressentir. Un contenu s'ouvre sur un niveau 3 ; un texte long en contient au moins deux.
- **Les chiffres inventés.** Une statistique du genre « la plupart des femmes de 40 ans » écrite sans source a déjà été recopiée par des automatismes. Dans le dossier, une fréquence est un compte réel de phrases (« dite dans une quinzaine d'appels »), jamais un pourcentage deviné.
- **Le client présenté comme fautif.** Les textes qui faisaient porter la faute au client le faisaient décrocher : il se sentait jugé. Le récit nomme un vrai ennemi extérieur, et le client reste le héros.
- **Les noms partent chez Google.** Seuls les paquets passés au contrôle anti-noms (`controle-verite`) vont dans un carnet. Le dossier lui-même reste dans le vault.
- **Les pensées les plus intimes sont rares.** Elles sortent dans les messages écrits tard le soir et dans les formulaires avant l'appel, plus que dans les appels. Le formulaire avant l'appel (questions « quand est-ce que ça a commencé ? », « dernier épisode ? », « qu'as-tu déjà essayé ? ») a rempli à lui seul deux sections entières du dossier d'origine : ce que la personne a déjà essayé, et ce qui la bloque selon elle.
- **Le corpus ne voit que ceux qui ont déjà demandé de l'aide.** Les personnes qui n'ont encore consulté personne manquent ; les sources publiques comblent en partie ce trou. Écris-le dans « Trous du dossier ».

## Entretien dans le temps
- Chaque nouvel appel, message ou formulaire ingéré passe par l'étape 3 : les phrases fortes entrent dans le dossier, les micro-moments dans la bibliothèque.
- Une fois par mois : relance `verifier-dossier.py`, remets à jour les compteurs de fréquence, ajoute une situation si une nouvelle revient souvent.
- Une fois par trimestre : compare les contenus qui ont le mieux marché aux pensées qu'ils utilisaient. Monte ces pensées en tête de la section 5 de leur fichier.

## Après
Mets à jour `wiki/maps/parcours.md` (brique `dossier-client-ideal` faite), une ligne dans `log.md`, et la mémoire (« tout contenu lit d'abord le dossier du client idéal »). Propose ensuite `voix-personnelle`.
