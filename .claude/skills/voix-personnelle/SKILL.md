---
name: voix-personnelle
description: "Construit wiki/maps/voix.md, la page qui décrit comment l'utilisateur écrit et parle, tirée de ses vrais textes et enregistrements, avec des règles mesurées et un contrôle automatique. Utiliser quand l'utilisateur dit « apprends ma voix », « écris comme moi », « ça ne sonne pas comme moi », « page voix ». Pas pour le contenu des offres (utiliser offre-et-echelle)."
---
# Voix personnelle

## Pourquoi
Un texte écrit par Claude sans modèle sonne comme tout le monde. Dans le système d'origine, les premières réponses aux clients étaient de longues lettres soignées alors que le fondateur répondait en deux lignes, avec un lien vidéo quand c'était lourd. Les clients l'auraient senti tout de suite. La voix a été mesurée sur un gros corpus de vrais messages : longueur, ouverture, ce qu'il fait quand c'est logistique, quand c'est grave. Depuis, Claude choisit le bon registre.

## Prérequis
- `entretien-fondateur` (au moins la séance 1).
- Des textes réels de l'utilisateur : emails, messages clients, posts, transcriptions d'appels ou de vidéos. Une vingtaine au minimum, une centaine idéalement.

## Interview
**Lis d'abord** : `wiki/business/fondateur.md`, tout ce que `raw/` contient d'écrit par l'utilisateur (cherche ses emails envoyés, ses posts, ses transcriptions), `wiki/appels/` s'il existe.

Puis demande :
1. Où sont tes textes les plus « toi » ? (Messages à des clients, posts, emails, vocaux.) Dépose-les dans `raw/voix/` ou dis-moi où les lire.
2. As-tu des enregistrements d'appels ou de vidéos ? Je peux les transcrire.
3. Quels mots ou tournures tu détestes lire sous ton nom ?
4. Tutoiement ou vouvoiement avec tes clients ? Et en public ?
5. Montre-moi un texte que tu trouves parfait chez toi, et un texte qui ne te ressemble pas.

Range les réponses dans `wiki/maps/voix.md`, section « Ce que tu m'as dit ».

## Construire
1. **Rassembler (Claude, 15 min).** Copie les textes dans `raw/voix/` (un fichier par source, jamais modifié ensuite). Si ce sont des fichiers audio ou vidéo, transcris-les avec l'outil installé au bloc A (ou propose Whisper en local) et range les transcriptions à côté.
2. **Classer (Claude, 20 min).** Pour chaque texte, note dans `outputs/voix/corpus.jsonl` une ligne : situation (logistique, conseil, mauvaise nouvelle, vente, encouragement, recadrage), longueur en mots, première phrase, dernière phrase, présence d'une question, d'un lien, d'une liste.
3. **Mesurer (Claude, 15 min).** Écris un petit script `scripts/voix_mesure.py` qui lit `corpus.jsonl` et sort, par situation : longueur médiane, part des messages qui finissent par une question, ouvertures les plus fréquentes, mots les plus fréquents propres à l'utilisateur (comparés à un texte neutre). Gabarit :
   ```python
   import json, statistics, collections, sys
   rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
   par = collections.defaultdict(list)
   for r in rows: par[r["situation"]].append(r)
   for sit, rs in sorted(par.items()):
       print(sit, len(rs), "textes, médiane", statistics.median(r["mots"] for r in rs), "mots,",
             round(100 * sum(r["question"] for r in rs) / len(rs)), "% finissent par une question")
   ```
4. **Écrire la page (Claude, 20 min).** `wiki/maps/voix.md` contient : la règle d'or en une phrase, les lois mesurées (« un message logistique fait une ou deux phrases »), une section par situation avec deux vrais exemples courts, la liste des mots interdits, la liste de ses expressions à lui. Les exemples restent internes : ils servent de modèle, ils ne se publient jamais.
5. **Contrôle automatique (Claude, 15 min).** Écris `scripts/voix_lint.py` qui lit un texte et signale : mots interdits, tirets longs, phrases de plus de 25 mots, longueur hors de la plage de la situation. Il sort 0 si propre, 1 sinon. Branche-le en fin de tout skill d'écriture.
6. **Test à l'aveugle (ensemble, 15 min).** Écris trois réponses à trois vrais messages anciens. Mélange-les avec les trois vraies réponses de l'utilisateur. Demande-lui de deviner lesquelles sont de lui. Corrige la page avec ce qu'il dit.

## Test
Au test à l'aveugle, l'utilisateur ne reconnaît pas au moins deux des trois réponses de Claude, et `voix_lint.py` sort 0 sur ses vrais textes.

## Pièges vécus
- **La lettre générique.** Sans mesure, Claude écrit long et poli partout. La mesure par situation a montré que la logistique se règle en une phrase et que les gros récits de douleur recevaient souvent une vidéo personnelle plutôt qu'un pavé.
- **Les citations réelles diffusées par erreur.** Les exemples de la page voix sont des preuves de style. Marque la section « interne, ne jamais publier ».
- **Corriger le français jusqu'à effacer la personne.** Garde ses tournures, enlève seulement les fautes dans ce qui se publie.
- **Un détecteur qui invente.** Un outil d'« humanisation » du système d'origine ajoutait des études chiffrées fausses. Le contrôle doit seulement signaler, jamais réécrire seul.

## Entretien dans le temps
- Chaque fois que l'utilisateur corrige un texte (« je ne dirais jamais ça »), ajoute la règle à `voix.md` et le mot à la liste du lint.
- Une fois par trimestre, ajoute ses textes récents au corpus et relance la mesure.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, et la mémoire (une ligne : « voix = wiki/maps/voix.md, lint = scripts/voix_lint.py »). Propose ensuite `plan-unique`.
