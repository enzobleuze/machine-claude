---
name: ingestion-appels
description: "Rapatrie les appels enregistrés (Fathom ou autre) dans raw/appels/, relie chaque appel à la fiche du client, puis construit la banque d'expérience : vraies situations, objections mot pour mot, meilleures phrases de la personne, par sujet. Utiliser quand l'utilisateur dit « récupère mes appels », « /pull-fathom », « qu'est-ce que mes clients disent vraiment », « construis la banque d'expérience ». Pas pour analyser un seul appel de vente en détail (bloc D, analyse d'appel)."
---
# Ingestion des appels enregistrés

## Pourquoi
Dans le système d'origine, des centaines d'heures d'appels dormaient dans l'outil d'enregistrement. Le contenu produit sonnait générique parce qu'il était écrit sans elles. Une fois les transcriptions rapatriées puis découpées en une banque d'expérience (situations réelles, objections dans les mots du client, phrases fortes du coach), tout le contenu a pu piocher dans du vécu. Un tirage tournant évite de ressortir toujours le même cas.

## Prérequis
- architecture-vault, ingestion-fichiers, securite-git-secrets.
- Un enregistreur d'appels. Fathom (offre gratuite possible) a une API simple. Autres options : Zoom, Google Meet, tl;dv, Otter, qui exportent des transcriptions en texte.
- Python 3.9+.
- Le consentement des personnes enregistrées, selon la loi de son pays. Demande-lui s'il l'a.

## Interview
Lis d'abord : `wiki/maps/architecture.md`, `wiki/clients/_index.md`, `wiki/maps/ingestion.md`.

Puis demande :
1. « Avec quoi enregistres-tu tes appels ? Depuis quand ? Combien environ ? »
2. « Quels types d'appels ? » (découverte, vente, suivi client, interne). Chaque type aura son étiquette.
3. « Quels grands sujets reviennent dans tes appels ? » 5 à 12 sujets, dans ses mots. Ce sont les sections de la banque.
4. « Tes clients sont-ils d'accord pour que leurs histoires servent, anonymisées, à ton contenu ? » Sans accord : la banque reste interne et ne nourrit que la compréhension, jamais une histoire reconnaissable.

Range les réponses dans `wiki/maps/appels.md` (outil, types, sujets, règle de confidentialité), avec 3 liens.

## Construire
1. **Clé (5 min, ses mains).** Fathom : Réglages > API Access > générer une clé. Claude crée `~/.claude/secrets/fathom.env` (Windows : `%USERPROFILE%\.claude\secrets\fathom.env`) et la personne y colle `FATHOM_API_KEY=<clé>`.
2. **Rapatrier (5 min).** Copie `outils/pull-fathom.py` vers `scripts/`, puis :
   ```bash
   python scripts/pull-fathom.py --depuis 2024-01-01
   ```
   Un fichier par appel dans `raw/appels/`. Relancer ne retélécharge rien. Autre outil : exporte les transcriptions en texte dans `raw/appels/` en gardant le même nom `AAAA-MM-JJ-titre-id.md` et un frontmatter `date`, `title`, `participants`.
3. **Inventaire (10 min).** Claude lit les en-têtes et écrit `wiki/sources/appels-inventaire.md` : un tableau date, type, personne (lien vers sa fiche), durée, sujet principal. Les appels sans fiche client correspondante sont listés à part.
4. **Fiches clients (15 min par lot de 10).** Pour chaque appel d'un client : section « Historique des appels » de `wiki/clients/<prenom-nom>.md`, une entrée datée de 3 à 5 lignes (où il en était, ce qui a bougé, prochaine étape). Lien vers le fichier raw.
5. **Banque d'expérience (20 min par lot).** Écris `wiki/maps/banque-experience.md`, une section par sujet, trois listes par section :
   ```markdown
   ### <Sujet>
   **Vraies situations (sans détail identifiant) :**
   - Description de la situation en 2 à 4 phrases. _(appel du AAAA-MM-JJ)_
   **Objections réelles (mot pour mot) :**
   - « phrase exacte du client » _(AAAA-MM-JJ)_
   **Phrases fortes de <la personne> (mot pour mot) :**
   - « phrase exacte » _(AAAA-MM-JJ)_
   ```
   Règles : citation exacte ou rien. Aucun nom, aucune ville, aucun détail qui permette de reconnaître quelqu'un dans la partie situations. Les objections vont aussi dans la page des objections fréquentes si elle existe (bloc D).
6. **Tirage tournant (5 min).** Ajoute dans la banque une ligne « Dernières utilisations » : chaque fois qu'un contenu pioche une situation, note la date et le sujet. Règle pour les skills de contenu : ne jamais reprendre deux fois de suite la même situation.
7. **Régularité (optionnel).** Tâche de nuit (bloc F) : `pull-fathom.py` chaque nuit, ingestion des nouveaux appels le lendemain.

## Test
`python scripts/pull-fathom.py` relancé affiche « 0 nouvel(s) appel(s) ». La banque a au moins une situation, une objection et une phrase forte par sujet de l'interview, chacune datée. Et `python scripts/lint_wiki.py` ne signale aucun lien mort vers raw/appels/.

## Pièges vécus
- Contenu public avec le vrai prénom d'un client et son histoire : risque légal. Partout en public, un prénom inventé et aucun détail traçable. La banque garde les dates, pas les noms, dans les situations.
- Résumés de l'outil d'enregistrement pris pour la vérité : ils lissent et inventent parfois. On cite la transcription, jamais le résumé automatique.
- Transcriptions mal orthographiées citées telles quelles : corrige l'orthographe évidente, jamais le sens.
- Appels internes ou personnels mêlés aux appels clients : l'étiquette de type les sépare, et les appels personnels ne vont pas dans la banque.

## Entretien dans le temps
Chaque mois, ajoute les nouveaux appels à la banque. Quand un sujet a moins de trois situations, signale-le : c'est un trou de terrain. Si la clé expire (code 1), recrée-la.

## Après
Coche la ligne `ingestion-appels` dans `wiki/maps/parcours.md`, entrée dans `log.md`, ligne « récupère mes appels » dans `wiki/maps/routage.md`, puis propose la source suivante de son interview, ou le bloc B si toutes sont branchées.
