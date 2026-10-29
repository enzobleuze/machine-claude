---
name: entretien-fondateur
description: "Mène l'entretien fondateur en plusieurs séances de 20 minutes (mission, histoire, client idéal avec ses mots exacts, offres, preuves, chiffres, temps disponible) et range tout dans wiki/business/. Utiliser quand l'utilisateur dit « on commence le business », « interroge-moi sur mon activité », « entretien fondateur », « reprends l'entretien ». Pas pour la voix d'écriture (utiliser voix-personnelle) ni pour fixer les objectifs chiffrés (utiliser plan-unique)."
---
# Entretien fondateur

## Pourquoi
Toutes les briques du bloc D ont besoin des mêmes faits : qui tu aides, ce que tu vends, ce que tu as déjà prouvé, combien tu gagnes, combien d'heures tu as. Dans le système d'origine, ces faits étaient éparpillés dans des dizaines de notes et Claude les redemandait à chaque conversation, ou pire les inventait. Un seul entretien, rangé en un seul endroit, règle les deux problèmes. Il se fait en séances courtes, parce qu'un entretien de trois heures ne se finit jamais.

## Prérequis
- Bloc A installé (le vault et sa mémoire existent).
- Aucun compte, aucun coût.

## Interview
**Lis d'abord**, pour ne rien redemander : `wiki/business/` s'il existe, `CLAUDE.md`, la mémoire (fichiers `user_*` et `project_*`), les notes de `raw/` qui parlent de l'activité (cherche « client », « offre », « prix », « témoignage »). Note ce que tu sais déjà et pose seulement les questions qui restent.

Pose les questions une à la fois, ou par deux quand elles vont ensemble. Reformule chaque réponse en une phrase et demande « c'est juste ? » avant de l'écrire. Garde les mots exacts de l'utilisateur entre guillemets.

**Séance 1 (20 min) : mission et histoire** → `wiki/business/fondateur.md`
1. Qu'est-ce que tu fais, dit comme à un ami qui ne connaît rien à ton métier ?
2. Pourquoi toi ? Quel moment de ta vie t'a amené là ?
3. Qu'est-ce que tu veux changer dans la vie des gens que tu aides ?
4. Qu'est-ce que tu refuses de faire, même si ça rapporte ?

**Séance 2 (20 min) : client idéal** → `wiki/business/client-ideal.md`
5. Décris la dernière personne que tu as vraiment aidée : âge, situation, ce qu'elle vivait le soir où elle t'a contacté.
6. Quelles phrases exactes tes clients disent-ils quand ils vont mal ? (Demande des messages, des emails, des notes d'appels. Copie mot à mot.)
7. Qu'est-ce qu'ils ont déjà essayé avant toi, et pourquoi ça n'a pas marché ?
8. Qu'est-ce qui les fait hésiter à acheter ?
9. Qui ne doit PAS devenir ton client ?

**Séance 3 (20 min) : offres et preuves** → `wiki/business/offres.md` et `wiki/business/preuves.md`
10. Liste tout ce que tu vends ou as vendu : nom, prix, durée, contenu, combien de fois vendu.
11. Qu'est-ce qui marche le mieux, et qu'est-ce que tu as arrêté ?
12. Quelles preuves as-tu : témoignages écrits, vidéos, résultats chiffrés, captures ? Où sont-elles ?
13. Lesquelles as-tu le droit de montrer en public, avec ou sans le prénom ?

**Séance 4 (20 min) : chiffres et temps** → `wiki/business/chiffres.md` (zone privée)
14. Combien as-tu encaissé sur les 12 derniers mois ? Par mois en moyenne ?
15. Combien de clients actifs aujourd'hui ? Combien de prospects en cours ?
16. D'où viennent tes clients (bouche à oreille, réseaux, pubs, site) ?
17. Combien d'heures par semaine as-tu VRAIMENT pour ton business, en comptant le reste de ta vie ?
18. Quels outils utilises-tu déjà (CRM, email, agenda, paiement, enregistrement d'appels) ?

Une réponse floue ou « je ne sais pas » s'écrit telle quelle avec « à vérifier ». Jamais de chiffre deviné.

## Construire
1. **Préparer (Claude, 5 min).** Crée `wiki/business/` avec les cinq fichiers vides ci-dessous, chacun avec un frontmatter `type: business`, `updated:`, `statut: en cours`. Écris dans `wiki/business/_entretien.md` la liste des 18 questions avec une case par question, cochée quand la réponse est rangée.
2. **Séance 1 (ensemble, 20 min).** Pose les questions 1 à 4. Écris `fondateur.md` avec les sections Mission, Histoire, Ce que je refuse. Coche les cases. Arrête-toi à 20 minutes même si tout n'est pas fini, et note où tu t'es arrêté.
3. **Séance 2 (ensemble, 20 min).** Questions 5 à 9. Dans `client-ideal.md`, fais une section « Ses mots exacts » où chaque phrase vient d'un vrai message, avec sa source (« email du 12/03 », « appel avec un client »). Si l'utilisateur a des captures ou des exports de messages, demande-lui de les déposer dans `raw/` et lis-les toi-même.
4. **Séance 3 (ensemble, 20 min).** Questions 10 à 13. `offres.md` : un tableau (nom, prix, durée, contenu, ventes passées, statut actif ou arrêté). `preuves.md` : une ligne par preuve avec son droit d'usage (public avec prénom, public anonyme, interne seulement).
5. **Séance 4 (ensemble, 20 min).** Questions 14 à 18. `chiffres.md` porte `confidentiel: true` dans son frontmatter. Ajoute dans `CLAUDE.md` la ligne : « wiki/business/chiffres.md est privé : aucun skill de contenu ne le lit. »
6. **Synthèse (Claude, 10 min).** Écris en haut de `fondateur.md` un résumé de 5 lignes : qui, pour qui, quoi, preuve principale, temps disponible. Ce résumé est ce que les autres skills lisent en premier. Montre-le à l'utilisateur et corrige jusqu'à son « oui ».

## Test
Les 18 cases de `_entretien.md` sont cochées ou marquées « à vérifier », et une nouvelle conversation qui lit seulement `fondateur.md` répond juste à « qui est mon client idéal et que je lui vends ? » sans poser de question.

## Pièges vécus
- **Les chiffres inventés se propagent.** Un faux chiffre sur un site (« des centaines de clients ») a été repris par des agents automatiques et recopié dans des brouillons. Ne range que des chiffres donnés par l'utilisateur, avec leur date.
- **Les mots du client se perdent dans la reformulation.** Claude a tendance à écrire « il se sent seul » au lieu de « je suis tout seul contre le monde ». Les textes qui touchent viennent des phrases brutes. Garde-les mot à mot.
- **Le vrai prénom d'un client dans une preuve publique** expose l'utilisateur légalement. Note le droit d'usage de chaque preuve dès l'entretien.
- **Un business qui a déjà vendu n'est pas un débutant.** Si l'utilisateur a des clients passés, l'histoire compte comme preuve : demande-la, même si l'activité est en pause.

## Entretien dans le temps
- À chaque nouvelle vente ou nouveau témoignage, mets à jour `preuves.md` et `chiffres.md`.
- Tous les trois mois, propose une séance de 20 minutes « qu'est-ce qui a changé ? » sur les questions 5, 10 et 17.

## Après
Mets à jour `wiki/maps/parcours.md` (brique entretien-fondateur faite), ajoute une ligne dans `log.md`, enregistre en mémoire le temps disponible par semaine (il sert à la règle des 4 %). Propose ensuite `dossier-client-ideal` (le client idéal mot à mot, matière de tout contenu), puis `voix-personnelle`.
