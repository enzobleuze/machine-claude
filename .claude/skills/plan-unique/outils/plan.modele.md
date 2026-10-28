---
title: "Plan unique : {{OBJECTIF_LONG_TERME}}"
type: strategie
status: actif
created: {{DATE_DU_JOUR}}
updated: {{DATE_DU_JOUR}}
# Le Cockpit lit ce bloc. Claude le met à jour à chaque revue. Les chiffres viennent de l'utilisateur, jamais inventés.
cap:
  libelle: "{{OBJECTIF_LONG_TERME_EN_MOTS}}"
  mensuel: {{REVENU_MENSUEL_VISE}}
  echeance: {{AAAA-MM-JJ}}
jalons:
  - {echeance: {{AAAA-MM-JJ}}, mensuel: {{REVENU_MENSUEL_JALON_1}}}
  - {echeance: {{AAAA-MM-JJ}}, mensuel: {{REVENU_MENSUEL_JALON_2}}}
trimestre:
  nom: "{{T1 2027}}"
  fin: {{AAAA-MM-JJ}}
  objectifs:
    - {titre: "{{Ventes signées}}", cible: {{N}}, actuel: {{N_OU_null}}, unite: "ventes"}
    - {titre: "{{Appels de vente tenus}}", cible: {{N}}, actuel: {{N_OU_null}}, unite: "appels"}
mois:
  cible: {{ENCAISSEMENT_VISE_CE_MOIS}}
semaine:
  debut: {{AAAA-MM-JJ_DU_LUNDI}}
  chose: "{{LA_PRIORITE_DE_LA_SEMAINE_EN_UNE_PHRASE}}"
---

# Plan unique

> Le seul plan. Tout ancien plan part en archive le jour où celui-ci est validé. Le Cockpit lit le bloc du haut et les deux sections suivantes.

## Semaine du {{JJ/MM}} au {{JJ/MM}}
Claude réécrit cette liste chaque lundi avec toi (« plan du lundi »). Chaque case dit qui la fait, combien de minutes, et le jour si c'est daté.
- [ ] {{Lundi JJ/MM}}, toi 20 min : {{action concrète}}
- [ ] Claude, sans ton temps : {{action}}
- [ ] Toi 15 min : valider {{ce que Claude a préparé}}

## Feuille de route
Les étapes dans l'ordre. La ligne marquée **PROCHAINE** est toujours la tâche suivante, et il n'y en a qu'une.

### Étape 1 : {{nom}} (fin visée le {{JJ/MM}})
Preuve de fin : {{phrase binaire qui dit quand l'étape est finie}}.
- [ ] **PROCHAINE** {{tâche}}
- [ ] {{tâche}}

### Étape 2 : {{nom}} (fin visée le {{JJ/MM}})
Preuve de fin : {{phrase binaire}}.
- [ ] {{tâche}}

## Décisions qui t'attendent
| Décision | Sujet | Reco de Claude |
|-|-|-|
| D1 | {{sujet}} | {{reco}} |

## Pourquoi ce cap
{{Mission et raison du chiffre, dans les mots de l'utilisateur. Lien vers wiki/business/fondateur.md.}}
