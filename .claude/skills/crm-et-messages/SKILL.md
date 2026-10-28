---
name: crm-et-messages
description: "Branche le CRM par son API (lecture d'abord), trie les messages entrants, prépare des brouillons dans la voix de l'utilisateur, met en place un moteur de DM à mots-clés (commentaire vers message privé) et vérifie les agents IA que le CRM installe d'office. Utiliser quand l'utilisateur dit « branche mon CRM », « qui m'a écrit ? », « trie mes messages », « mot-clé en commentaire », « DM automatique », « un brouillon bizarre est apparu ». Pas pour les séquences d'emails (utiliser email-liste)."
---
# CRM et messages

## Pourquoi
Les prospects écrivent partout : réseaux, chat du site, email, SMS. Dans le système d'origine, un CRM tout-en-un (GoHighLevel) centralisait ces canaux, et Claude le lisait par son API pour dire qui attendait une réponse et préparer les brouillons. Un moteur de mots-clés transformait un commentaire (« GUIDE », par exemple) en message privé avec la bonne ressource. Deux accidents ont appris à surveiller le CRM lui-même : deux robots qui répondaient sur le même fil, et des agents installés d'office qui ont créé des brouillons pleins de faux chiffres.

## Prérequis
- `fiches-clients`, `voix-personnelle`, `repondre-client`.
- Un CRM avec API : GoHighLevel, HubSpot, Brevo, Systeme.io, ou autre (option au choix de l'utilisateur). Coût selon l'offre.
- Le bloc A pour ranger les secrets hors du vault (par exemple `~/.claude/secrets/crm.env`), jamais dans un fichier suivi par git.

## Interview
**Lis d'abord** : `wiki/business/fondateur.md` (outils déjà utilisés), `wiki/clients/_index.md`, la mémoire (outils, comptes), tout fichier `wiki/maps/crm*.md`.

Puis demande :
1. Quel CRM utilises-tu, ou veux-tu utiliser ? Sur quels canaux tes prospects t'écrivent-ils ?
2. Peux-tu créer une clé d'API ? (Je te guide clic par clic, et c'est toi qui la colles dans le fichier secret : je ne tape jamais un secret.)
3. Veux-tu que je lise seulement, ou aussi que je dépose des brouillons ? (Envoyer reste ton geste, sauf règle écrite.)
4. Utilises-tu déjà des mots-clés en commentaire ? Lesquels, vers quelle ressource ?
5. Y a-t-il déjà des automatisations ou des agents IA actifs dans ton CRM ?

Range dans `wiki/maps/crm.md`.

## Construire
1. **Clé d'API (utilisateur guidé, 10 min).** Ouvre avec lui la page des clés de son CRM (dans GoHighLevel : Réglages, puis Clés d'API privées ou Intégrations privées ; ailleurs, cherche « API key » dans les réglages). Donne seulement les droits de lecture des contacts et des conversations au début. Il colle la clé dans `~/.claude/secrets/crm.env` sous la forme `CRM_API_KEY=…`. Ajoute ce dossier à la règle « jamais lu par un skill de contenu » du bloc A.
2. **Lecture et test (Claude, 15 min).** Écris `scripts/crm_lire.py` (stdlib, `urllib.request`) qui lit la clé, appelle la route « conversations récentes », et sort pour chaque conversation : nom, canal, date du dernier message entrant, dernier message sortant, et s'il attend une réponse. Gère les erreurs lisiblement (clé refusée, quota, réseau) et donne un en-tête `User-Agent` (certains CRM refusent les requêtes sans). Teste : la sortie doit lister les vraies dernières conversations.
3. **Tri du matin (Claude, 10 min).** Une commande « qui m'a écrit ? » lit le CRM, rapproche chaque conversation de sa fiche (`crm_id` ou email), met `attend_reponse` dans la fiche quand le dernier message vient de la personne, et classe en trois piles : à répondre aujourd'hui, à relire, rien à faire. Les envois de masse et les comptes de test ne comptent pas.
4. **Brouillons (Claude, 5 min par message).** Pour chaque message à répondre, applique `repondre-client`. Si l'utilisateur a donné le droit, dépose le texte en brouillon dans le CRM. Sinon montre-le pour copier.
5. **Mots-clés en commentaire (ensemble, 20 min).** Dans `wiki/maps/mots-cles.md`, un tableau : mot, variantes et fautes de frappe, ressource envoyée, où on l'utilise. Avant d'activer un mot, teste-le contre une cinquantaine de vraies phrases de douleur de `client-ideal.md` : un mot qui part par hasard sur une phrase hors sujet est à changer. Un mot qui mène à un appel doit être un mot qu'on n'écrit jamais par hasard.
6. **Moteur de DM (selon l'outil, 20 min par étape).** Option A : la fonction native du CRM (commentaire vers DM) si elle couvre tes réseaux. Option B : un outil dédié (ManyChat par exemple). Option C : ton propre petit moteur sur l'API officielle de la plateforme, plus long à monter, sans coût par contact. Dans tous les cas : mode écoute d'abord (rien n'est envoyé), test avec un second compte, message de détresse traité en premier et transmis à l'utilisateur, puis ouverture à tous.
7. **Un seul robot par fil (Claude, 10 min).** Liste toutes les automatisations et tous les agents qui peuvent répondre sur chaque canal. Sur un même canal, un seul répond. Écris la carte dans `crm.md`.
8. **Agents installés d'office (Claude, 10 min, puis chaque mois).** Certains CRM ajoutent seuls des agents IA (contenus, rapports, publications). Liste-les par l'API ou dans l'interface, montre la liste à l'utilisateur, et désactive avec son accord ceux qui écrivent ou publient sans lui.
9. **Workflows que l'API ne crée pas (ensemble, 15 min).** Plusieurs CRM ne créent pas de workflow par l'API. Claude écrit le prompt complet pour l'assistant de workflows du CRM, l'utilisateur le colle, puis colle le résumé obtenu ici, et Claude vérifie étape par étape.

## Test
`crm_lire.py` liste les vraies conversations du jour, le tri du matin met `attend_reponse` dans les bonnes fiches, et un commentaire test avec un mot-clé reçoit la bonne ressource en message privé sur le compte de test.

## Pièges vécus
- **Deux robots sur un fil.** Un agent IA du CRM sans canal réglé répondait partout, par-dessus le moteur de mots-clés. Sur Instagram, une seule app peut avoir la main sur une conversation : la première qui répond la garde. Règle chaque canal avant d'ouvrir.
- **Les agents installés d'office.** Un agent ajouté par le CRM a créé une série de brouillons de publication avec les faux chiffres du site. Un brouillon que personne n'a demandé vient d'un agent : cherche-le et désactive-le.
- **Le faux test compté comme vrai.** Le bouton de test d'une plateforme envoie des identifiants fictifs que le moteur a pris pour un vrai inconnu. Exclus-les dans le code.
- **Le mot-clé qui collisionne.** Le mot « appel », qui menait à la prise de rendez-vous, partait sur des plaintes ordinaires qui contenaient ce mot. Il a été remplacé par un mot qu'on n'écrit jamais par hasard. Teste chaque mot sur de vraies phrases avant de l'activer.
- **« Message automatique » en tête.** Un DM qui s'annonce robot casse la confiance. Écris des messages courts, utiles, au ton de la conversation, avec des boutons testés.
- **Claude qui tape un secret.** Jamais. L'utilisateur colle les clés lui-même.

## Entretien dans le temps
- Tous les matins (bloc F) : tri du matin, et le Cockpit montre qui attend.
- Chaque mois : liste des agents et automatisations actifs, comparée à la carte de `crm.md`.
- À chaque nouveau mot-clé : test de collision avant activation.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (CRM choisi, droits de la clé, règle d'envoi). Propose ensuite `email-liste`.
