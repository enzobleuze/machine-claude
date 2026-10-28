---
name: controle-voix
description: "Installe le lint de voix : un script qui contrôle chaque texte contre les règles dures et mesurables de la voix de l'utilisateur (mots et tournures interdits, tirets longs, répétitions en début de phrase), règles écrites dans un fichier JSON rempli pendant l'interview. Utiliser quand l'utilisateur dit « ça sonne IA », « Claude répète les mêmes tics », « vérifie mon style avant de publier ». Pas pour la vérité des chiffres (utiliser controle-verite), pas pour écrire le guide de voix (bloc D)."
---
# Le lint de voix

## Pourquoi
Un guide de voix se lit une fois et s'oublie ; un script se lance à chaque texte. Dans le système d'origine, les tics d'écriture de l'IA revenaient sans cesse (tirets longs, « ce n'est pas X, c'est Y », trois phrases qui commencent pareil, anglicismes) malgré les consignes. Un lint sans modèle de langue, qui sort 1 dès qu'une règle dure tombe, a réglé ça : la chaîne de production le lance en dernier, et un texte qui échoue ne part pas.

## Prérequis
- Le guide de voix de l'utilisateur (bloc D, entretien fondateur et voix) et quelques textes qu'il a écrits lui-même.
- Python 3.8 ou plus.

## Interview
Lis d'abord : le guide de voix du vault, 3 à 5 textes écrits par l'utilisateur (pas par Claude), et les corrections qu'il a déjà faites sur des textes de Claude (mémoire `feedback_*`).

Puis demande, en petit lot :
1. « Quels mots tu ne veux JAMAIS voir dans tes textes ? » (exemples à proposer : anglicismes, mots de jargon, tics de ta région que tu ne veux pas à l'écrit.) Pour chacun : « Par quoi on le remplace, ou on le signale seulement ? »
2. « Quelles tournures te font dire " ça, c'est écrit par une IA " ? » (proposer : le tiret long, « ce n'est pas X, c'est Y », trois phrases de suite qui commencent par le même mot, la liste de trois en rythme.)
3. « Tu tutoies ou tu vouvoies ton client ? » (une règle mesurable : un motif sur « vous » ou « tu », selon la réponse.)
4. « Y a-t-il des mots sensibles dans ton métier qu'il faut remplacer ? »
5. « Quand un texte cite quelqu'un mot pour mot, on laisse la citation intacte ? » (par défaut : oui, les lignes « > » sont signalées, jamais corrigées.)

Ce qui ne se mesure pas (« trop froid », « pas assez moi ») reste dans le guide de voix. Range les règles mesurables dans `regles-voix.json`.

## Construire
1. **Poser l'outil** (Claude) : copier `outils/lint_voix.py` dans `scripts/lint_voix.py` du vault. `python scripts/lint_voix.py selftest` doit imprimer `selftest OK`.
2. **Écrire les règles** (Claude) : copier `outils/regles-voix.modele.json` en `regles-voix.json` à la racine du vault, puis le remplir :
   - `mots_interdits` : un objet par mot, avec `remplacer_par` quand le remplacement est sûr partout, sans quand il dépend du contexte (alors le script signale et l'humain ou Claude réécrit).
   - `motifs_interdits` : une expression régulière par tournure, avec `message` (pourquoi) et `niveau` (`dur` bloque, `alerte` signale). Le modèle contient déjà l'antithèse « ce n'est pas X, c'est Y ».
   - `anaphore` : `min` (3 par défaut) et les petits mots à ignorer en début de phrase.
   Claude teste chaque nouvelle règle sur une phrase qui doit tomber et une qui doit passer, avant de la garder.
3. **Lancer** :
   ```
   python scripts/lint_voix.py <texte>                 # 0 propre, 1 règle dure tombée, 2 problème d'usage
   python scripts/lint_voix.py <texte> --fix           # applique les remplacements sûrs, puis contrôle
   python scripts/lint_voix.py <texte> --json          # pour les scripts
   ```
4. **Brancher** (Claude) : dernière étape de chaque skill qui écrit pour les clients, siège Voix du board, et chaque skill de publication avant la porte. Règle dans `CLAUDE.md` : « Tout texte pour les clients sort 0 au lint de voix avant d'être montré. »
5. **Relecture humaine de ce que le script ne voit pas.** Écrire dans le guide de voix les deux ou trois tics que le lint rate encore (exemple : la liste de trois en rythme, difficile à mesurer sans faux positifs), et demander à Claude de les relire à la main sur les textes longs.

## Test
Sur un texte piège (un tiret long, une tournure interdite, trois phrases de suite au même premier mot, un mot banni) : `lint_voix.py` sort 1 et nomme chaque ligne. Sur un vrai texte de l'utilisateur, relu et approuvé par lui : il sort 0. Si ce texte approuvé sort 1, une règle est trop large : la resserrer.

## Pièges vécus
- **Un mot exclu, un trou dans le filet.** Le premier lint ignorait les pronoms en début de phrase, pour éviter les faux positifs. Résultat : « Tu... Tu... Tu... », la répétition la plus fréquente, passait. Ici les pronoms ne sont jamais exclus par défaut.
- **Corriger une citation.** Remplacer un mot dans une phrase citée mot pour mot la rend fausse. Les lignes « > » sont signalées, jamais corrigées.
- **Les URL et le code.** Un double tiret dans une adresse web ou une commande n'est pas une faute de style. Le script les ignore.
- **Le remplacement automatique aveugle.** Certains mots ont un sens correct selon le contexte. Sans `remplacer_par`, le script signale seulement, et la phrase se réécrit avec du sens.
- **Un juge de style par modèle de langue varie.** Pour les règles dures, un script déterministe : même texte, même verdict, chaque fois. Le modèle reste utile pour le reste du guide, en relecture.
- **L'outil « anti-IA » qui invente.** Un outil qui réécrivait les textes pour les rendre « plus humains » ajoutait des faits inventés. Le lint ne réécrit rien d'autre que les remplacements que l'utilisateur a validés.

## Entretien dans le temps
- Chaque fois que l'utilisateur corrige un tic dans un texte de Claude : se demander s'il se mesure. Si oui, une règle de plus dans `regles-voix.json`, testée, et une ligne dans le selftest si c'est un cas délicat.
- Une fois par trimestre : relancer le lint sur les textes publiés du trimestre. Une règle qui ne tombe jamais peut sortir ; une alerte qui tombe souvent sur de bons textes se retire.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (« le lint de voix est la dernière étape de tout texte »). Propose ensuite `board-textes` s'il n'est pas fait, sinon `skills-marketing`.
