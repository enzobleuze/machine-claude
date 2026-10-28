---
name: fiches-clients
description: "Crée une fiche par client et par prospect dans wiki/clients/ (frontmatter lisible par le Cockpit, situation, objectifs, journal, appels, paiements) et consolide les anciens dossiers éparpillés. Utiliser quand l'utilisateur dit « crée la fiche de X », « range mes clients », « importe mes clients », « consolide les dossiers ». Pas pour répondre à un client (utiliser repondre-client)."
---
# Fiches clients et dossiers consolidés

## Pourquoi
Quand un client écrit, la bonne réponse dépend de tout ce qu'on sait de lui. Dans le système d'origine, l'information vivait dans un CRM, un outil de notes, des enregistrements d'appels et des messages, et Claude répondait sans contexte. Une fiche par personne, au même format, a réglé ça. Le Cockpit lit les mêmes fiches pour dire qui attend une réponse.

## Prérequis
- Bloc A (vault, règle des zones privées).
- `entretien-fondateur` (offres, pour remplir le champ offre).
- Outil joint : `outils/fiche-client.modele.md`.
- Optionnel : export du CRM ou de l'outil de notes (CSV, Notion, tableur).

## Interview
**Lis d'abord** : `wiki/clients/` s'il existe, `raw/` (cherche exports CSV, dossiers clients, « contrat », « paiement »), `wiki/business/offres.md`.

Puis demande :
1. Où sont tes clients aujourd'hui ? (CRM, tableur, carnet, outil de notes, boîte mail.) Peux-tu exporter la liste dans `raw/clients/` ?
2. Combien de clients actifs, d'anciens, de prospects en cours ? Juste un ordre de grandeur.
3. Pour un client, qu'est-ce que tu veux retrouver en 10 secondes avant de lui répondre ?
4. Est-ce que tes clients ont des enregistrements d'appels ? Où ?
5. Qui n'a pas le droit de voir ces fiches ? (Elles restent dans le vault, jamais partagées.)

Range les règles dans `wiki/clients/_index.md`.

## Construire
1. **Règles de la zone (Claude, 5 min).** Crée `wiki/clients/_index.md` : format des noms de fichier (`prenom-nom.md`, sous-dossier `leads/` pour les prospects si tu préfères), règle « vrais noms en interne, jamais un vrai prénom avec son histoire en public », règle « les coordonnées ne sortent jamais du vault ». Ajoute dans `CLAUDE.md` : « wiki/clients/ est privé : aucun skill de contenu public ne le lit, sauf en anonymisant. »
2. **Une première fiche (ensemble, 10 min).** Copie `outils/fiche-client.modele.md` vers `wiki/clients/<prenom-nom>.md` pour un client actif que l'utilisateur connaît bien. Remplis avec lui. Montre-lui la fiche et ajuste les sections à son métier (une boulangère n'a pas de « Appels » mais a des « Commandes »).
3. **Import en lot (Claude, 20 min par lot de 20).** Lis l'export de `raw/clients/`. Pour chaque ligne, crée la fiche avec ce qui est connu. Un champ inconnu reste `null` ou « à documenter ». Ne recopie jamais un statut sans vérifier : un « actif » d'un vieil export peut être fini depuis longtemps. Mets `statut: à vérifier` quand la dernière date connue a plus de trois mois.
4. **Consolider les doublons (Claude, 10 min).** Cherche les fiches qui parlent de la même personne (même email, même nom avec accent ou sans, suffixe « -2 »). Fusionne dans la plus complète, garde l'historique, et laisse dans l'autre une ligne « fusionnée dans [[…]] » plutôt que de la supprimer.
5. **Relier les appels (Claude, 10 min).** Si l'utilisateur a des enregistrements, ajoute dans la section Appels de chaque fiche un lien vers `wiki/appels/<date>-<prenom>.md` (créé par `appels-analyse`).
6. **Ce qui manque (Claude, 5 min).** Écris en bas de `_index.md` la liste des fiches actives sans objectifs, sans dernier échange ou sans paiement noté. L'utilisateur la complète quand il veut, par lots de 10 minutes.

**Champs que le Cockpit lit** (garde-les exacts) : `type` (client ou lead), `statut`, `attend_reponse` (date de son message sans réponse, `null` sinon), `prochain_pas`, `dernier_echange`.

## Test
Chaque client actif a une fiche dont le frontmatter se lit sans erreur (`python scripts/cockpit/cockpit_build.py ligne` ne signale aucune « Fiche illisible »), et Claude répond à « où en est <prénom> ? » en lisant seulement sa fiche.

## Pièges vécus
- **Le statut figé d'un import.** Des fiches importées disaient « actif » alors que le suivi était fini depuis des mois. Le statut se recalcule à partir des dates réelles, ou se marque « à vérifier ».
- **L'envoi de masse compté comme échange.** Un message envoyé à toute la liste n'est pas un échange avec la personne. `dernier_echange` = dernier message reçu de lui, appel tenu ou rendez-vous pris.
- **Les vrais prénoms dans le contenu public.** Une histoire de client racontée dans un post doit changer le prénom et tout détail traçable.
- **Les fiches de proches.** Un proche de l'utilisateur n'est pas un client, même s'il est dans le CRM. Ne crée pas de fiche sans accord.

## Entretien dans le temps
- Après chaque appel ou échange important, ajoute une ligne au Journal (le skill `repondre-client` et `appels-analyse` le font).
- Une fois par mois, Claude relance l'étape 6 et propose 10 minutes de complétion.
- Si le CRM est branché (`crm-et-messages`), une tâche de nuit peut régénérer un bloc CRM dans chaque fiche, entre deux balises, sans toucher au reste.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`. Propose ensuite `appels-analyse` si l'utilisateur fait des appels, sinon `repondre-client`.
