---
name: email-liste
description: "Monte la liste email : import propre, séquence de bienvenue, sortie automatique (STOP) dès qu'une personne prend rendez-vous ou achète, et lettre régulière dans la voix de l'utilisateur, avec test avant chaque envoi réel. Utiliser quand l'utilisateur dit « ma liste email », « séquence de bienvenue », « écris ma newsletter », « importe mes abonnés », « change d'outil d'email ». Pas pour les messages privés (utiliser crm-et-messages)."
---
# Liste email, bienvenue et lettre

## Pourquoi
La liste email est le seul public qui t'appartient. Dans le système d'origine, plus d'un millier d'abonnés vivaient dans un ancien outil, avec des centaines d'emails écrits au fil des années. La migration vers le CRM a appris trois choses : importer les anciens contacts en mode « ne pas déranger » pour ne pas les inonder, construire une seule sortie STOP qui retire des séquences quiconque prend rendez-vous ou achète, et tester chaque séquence sur un contact de test avant les vrais envois.

## Prérequis
- `voix-personnelle`, `offre-et-echelle` (ce vers quoi les emails mènent).
- Un outil d'email : celui du CRM (`crm-et-messages`), ou un outil dédié (MailerLite, Brevo, Kit, au choix). Un domaine d'envoi authentifié (SPF, DKIM, DMARC) : Claude guide les réglages.
- Bloc C : le board des textes, pour chaque email.

## Interview
**Lis d'abord** : `raw/` (exports d'emails passés, statistiques d'ouverture), `wiki/maps/crm.md`, `wiki/business/client-ideal.md`, `echelle-offres.md`.

Puis demande :
1. Combien d'abonnés as-tu, où, et d'où viennent-ils ?
2. Les anciens ont-ils reçu un email récemment ? (Sinon, on les réveille doucement ou on les laisse en « ne pas déranger ».)
3. Que reçoit un nouvel inscrit aujourd'hui ?
4. Quel est le but de la séquence : rendez-vous, achat, ou inscription à un événement ?
5. À quel rythme veux-tu écrire une lettre ? Une par semaine est un bon plancher, une par mois un minimum.
6. Ton domaine d'envoi est-il déjà authentifié ?

Range dans `wiki/maps/email.md`.

## Construire
1. **Authentifier le domaine (utilisateur guidé, 20 min).** Dans l'outil d'email, ouvre la page du domaine d'envoi. Copie chaque enregistrement DNS demandé (SPF, DKIM, DMARC) chez l'hébergeur du domaine, champ par champ. Claude vérifie ensuite avec `nslookup -type=TXT _dmarc.<domaine>` (Windows) ou `dig TXT _dmarc.<domaine>` (Mac, Linux).
2. **Import propre (Claude, 15 min).** Si l'outil a une API, Claude importe par l'API. Sinon il prépare un CSV propre (doublons retirés, adresses invalides retirées, étiquette de source). Les contacts qui n'ont rien reçu depuis longtemps entrent en « ne pas déranger » jusqu'à une campagne de réveil décidée par l'utilisateur.
3. **Sortie STOP (ensemble, 15 min, une seule fois).** Une automatisation unique : dès qu'un contact prend rendez-vous, achète ou se désinscrit, il sort de toutes les séquences. Si l'API ne crée pas d'automatisation, Claude écrit le prompt pour l'assistant de l'outil et vérifie le résultat (voir `crm-et-messages`, étape 9).
4. **Séquence de bienvenue (Claude, 20 min par email).** Cinq à sept emails sur deux semaines : livraison de la ressource promise, histoire du fondateur, une idée forte qui change sa façon de voir, une preuve réelle, une invitation claire vers la marche suivante de l'échelle. Chaque email part de ses mots exacts (`client-ideal.md`) et d'une expérience vraie (`wiki/maps/banque-experience.md`). Passe chaque email au board, puis à `voix_lint.py`. Range dans `outputs/emails/bienvenue/`.
5. **Tester (Claude et utilisateur, 10 min).** Inscris un contact de test (une adresse de l'utilisateur avec `+test`). Vérifie : chaque email arrive, le prénom s'affiche, les liens marchent, la sortie STOP coupe la séquence quand le contact de test prend un faux rendez-vous. Seulement après : publication.
6. **La lettre (Claude, 20 min par lettre).** Une lettre à la fois, sur le sujet de la semaine (bloc E si installé). Objet court et concret, une seule idée, une seule invitation. Brouillon déposé dans l'outil, envoi par l'utilisateur ou programmé après son accord.
7. **Liste de contrôle avant chaque envoi réel (Claude, 5 min).** Domaine authentifié, segment correct, contacts en « ne pas déranger » exclus, test reçu, liens vérifiés, aucun tiret long, board passé.

## Test
Le contact de test reçoit toute la séquence de bienvenue, sort de la séquence dès qu'il prend un faux rendez-vous, et l'en-tête de l'email reçu montre DMARC « pass ».

## Pièges vécus
- **Inonder les anciens.** Un import sans précaution envoie la séquence complète à des gens qui ne se souviennent plus de toi, et les plaintes pour courrier indésirable abîment ton domaine d'envoi. Importe-les en « ne pas déranger ».
- **Vendre à quelqu'un qui a déjà acheté.** Sans sortie STOP, un client recevait encore « réserve ton appel ». Une seule automatisation STOP règle tout.
- **Publier sans test.** Un prénom vide ou un lien cassé sur la liste entière ne se rattrape pas. Le test sur un contact de test est obligatoire.
- **Copier les meilleurs objets.** Les objets qui ouvraient le mieux étaient personnels et concrets. Les recettes d'objets génériques ne marchaient pas dans cette voix.

## Entretien dans le temps
- Chaque semaine : la lettre (plancher : une par mois).
- Chaque mois : taux d'ouverture et de clic par email de la bienvenue ; l'email le plus faible est réécrit.
- Après chaque changement d'automatisation : refaire le test de l'étape 5.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (outil d'email, rythme de la lettre). Propose ensuite `tunnel-et-quiz`.
