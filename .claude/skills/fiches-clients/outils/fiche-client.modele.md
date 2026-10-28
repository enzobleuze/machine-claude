---
title: "{{Prénom Nom}}"
type: client            # client (a payé) ou lead (n'a jamais payé)
statut: actif           # actif, ancien, prospect, perdu
offre: "{{nom de l'offre achetée, ou vide}}"
date_debut: {{AAAA-MM-JJ}}
valeur_contrat: {{montant ou null}}
dernier_echange: {{AAAA-MM-JJ}}   # dernier message entrant, appel tenu ou rendez-vous pris (jamais un envoi de masse)
attend_reponse: null    # date de son message sans réponse ; null quand tu as répondu
prochain_pas: "{{la prochaine chose à faire avec lui, en une phrase}}"
source: "{{d'où il vient : vidéo, mot-clé, recommandation, pub}}"
crm_id: null            # identifiant du contact dans ton CRM, si tu en as un
tags: [client]
---

# {{Prénom Nom}}

## Situation de départ
{{Ce qu'il vivait en arrivant, avec SES mots exacts entre guillemets.}}

## Objectifs
- {{objectif 1, mesurable}}

## Ce qui compte pour lui
{{Prénoms des proches, métier, contraintes, ce qu'il aime. Les détails qu'on « relie » plus tard (« comment s'est passé l'anniversaire de ta fille ? »).}}

## Journal
Une ligne par échange, la plus récente en haut.
- **{{AAAA-MM-JJ}}** ({{appel, message, email}}) : {{ce qui s'est dit, ce qui a été décidé}}

## Appels
- **{{AAAA-MM-JJ}}** : {{lien vers l'enregistrement ou l'analyse dans wiki/appels/}}

## Paiements et contrat
- Offre : {{nom}}, {{prix}}, {{plan de paiement}}
- Paiements reçus : {{dates et montants, ou « à vérifier »}}
- Contrat : {{lien ou « absent »}}

## Coordonnées
{{email, téléphone. Cette section ne sort jamais du vault.}}

## Voir aussi
- [[wiki/clients/_index]]
