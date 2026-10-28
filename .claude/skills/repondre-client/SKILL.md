---
name: repondre-client
description: "Prépare la réponse à un message de client ou de prospect dans la voix de l'utilisateur : lit sa fiche d'abord, choisit le bon registre (court, logistique, vidéo, fond), passe le mode léger du board, puis met la fiche à jour. Utiliser quand l'utilisateur colle un message de client, dit « réponds à X », « aide-moi à répondre », « qu'est-ce que je lui dis ? ». Pas pour une relance de prospect qui n'a pas acheté (utiliser appel-de-vente, partie relance)."
---
# Répondre à un client

## Pourquoi
Répondre vite et juste à chaque personne qui écrit est ce qui garde un client et ce qui en fait signer un nouveau. Dans le système d'origine, les premières réponses de Claude étaient des lettres longues et génériques. Un test à l'aveugle a montré trois manques : le client parlait d'autre chose que du sujet principal et Claude refusait d'y aller, Claude restait doux quand le client faisait l'inverse de ce qui était convenu, et il ne citait pas les ressources du programme par leur nom. Lire la fiche d'abord et choisir le registre a corrigé les trois.

## Prérequis
- `fiches-clients`, `voix-personnelle`.
- Bloc C : `board-textes` en mode léger (sièges : le bibliothécaire du vault, l'expert de fond de ton domaine, l'agent client idéal). Sans le bloc C, fais au moins la relecture voix et la vérification des faits.

## Interview
**Lis d'abord** : la fiche du client (`wiki/clients/<prenom-nom>.md`, en entier), ses derniers appels dans `wiki/appels/`, `wiki/maps/voix.md`, `wiki/business/offres.md` (ce à quoi il a droit).

Questions, seulement la première fois que le skill tourne :
1. Dans quels cas réponds-tu en une phrase, en vocal, en vidéo, ou avec un long message ?
2. Y a-t-il des sujets où tu veux toujours relire avant envoi ? (Santé, argent, crise.)
3. Quelles ressources de ton offre veux-tu que je cite par leur nom ?
4. En cas de détresse grave (danger pour la personne ou pour d'autres), quel est ton protocole et quel numéro d'urgence donnes-tu ?

Range dans `wiki/maps/voix.md`, section « Répondre à un client ».

## Construire
Ce skill se joue à chaque message. Étapes :
1. **Sécurité d'abord (Claude, 1 min).** Si le message parle de danger pour lui ou pour quelqu'un, applique le protocole de la question 4 avant tout le reste, et préviens l'utilisateur en tête de réponse.
2. **Lire la fiche (Claude, 2 min).** Situation, objectifs, ce qu'il a déjà essayé, dernier échange, prochain pas. Relie un détail du passé quand il éclaire (« la dernière fois tu m'as parlé de ta fille »).
3. **Choisir le registre (Claude, 1 min).** Logistique (accès, rendez-vous, paiement) : une ou deux phrases et le lien. Question simple : réponse courte, puis une question. Long récit de douleur : propose un vocal ou une vidéo personnelle à l'utilisateur plutôt qu'un pavé. Fond : la réponse de la méthode, en liste numérotée quand ce sont des actions. Chaque question posée par le client reçoit sa réponse.
4. **Écrire (Claude, 5 min).** Dans la voix mesurée. Si le client fait le contraire de ce qui était convenu, dis-le clairement et avec respect, dosé selon l'historique. Jamais de proposition commerciale quand le client va mal. Si un appel est déjà prévu, réponds au fond maintenant et garde le reste pour l'appel.
5. **Mode léger du board (Claude, 3 min).** Fais relire par les sièges du mode léger. Corrige. Lance `scripts/voix_lint.py` sur le texte. La logistique pure est exemptée.
6. **Montrer, puis envoyer avec accord (ensemble, 2 min).** Montre la réponse et une ligne « pourquoi ce registre ». L'utilisateur envoie, ou dit « envoie » si `crm-et-messages` est branché ; dans ce cas Claude dépose un brouillon dans le CRM et l'utilisateur appuie sur envoyer, sauf accord écrit pour ce type de message.
7. **Mettre la fiche à jour (Claude, 1 min).** Ligne au Journal, `attend_reponse: null`, `dernier_echange` à la date de son message, `prochain_pas` mis à jour.

## Test
Sur trois vrais messages anciens, l'utilisateur juge les trois réponses « je l'aurais envoyée », et la fiche de chaque client a sa ligne de Journal et `attend_reponse: null`.

## Pièges vécus
- **« Ce n'est pas mon domaine. »** Le client parlait de son travail ou de sa santé, Claude refusait d'en parler. L'utilisateur voulait aider sur toute la vie de la personne. Demande son périmètre une fois et respecte-le.
- **La lettre générique.** Sans fiche, la réponse pouvait aller à n'importe qui. Un détail réel du dossier change tout.
- **Le paquet complet à chaque fois.** Tout donner d'un coup noie la personne. Une ou deux actions, la suite au prochain échange.
- **Le message envoyé sans relecture.** Tout texte qui part au client passe par l'utilisateur, sauf règle écrite contraire.

## Entretien dans le temps
- Chaque correction de l'utilisateur devient une règle dans `voix.md`, section « Répondre à un client ».
- Le Cockpit affiche chaque matin qui attend une réponse depuis plus de 2 jours.

## Après
Mets à jour `wiki/maps/parcours.md` (première fois seulement), `log.md`. Propose ensuite `offre-et-echelle`.
