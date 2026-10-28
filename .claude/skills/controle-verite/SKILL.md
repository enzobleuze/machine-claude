---
name: controle-verite
description: "Installe les contrôles de vérité qui passent sur tout texte avant publication : zéro chiffre inventé (chaque chiffre trace vers une source), attributions sourcées (une personne citée a sa fiche source, pas de « des études montrent »), zéro nom de client réel en public, plus un outil pour pseudonymiser les paroles de clients. Utiliser quand l'utilisateur dit « Claude invente des chiffres », « vérifie ce texte avant que je publie », « anonymise mes clients ». Pas pour le style (utiliser controle-voix)."
---
# Les contrôles de vérité

## Pourquoi
Un modèle de langue écrit des chiffres plausibles avec aplomb. Dans le système d'origine, un article publié prêtait à un auteur de référence des délais précis qu'il n'avait jamais écrits : le texte « sonnait » juste, et il était faux. Depuis, trois règles dures passent sur chaque texte avant publication, par un script qui ne se laisse pas convaincre : tout chiffre vient d'une source ou devient une formule qualitative (« quelques jours », « la plupart ») ; toute personne citée a une fiche source ; aucun vrai nom de client n'apparaît en public.

## Prérequis
- Python 3.8 ou plus.
- Les fiches sources des auteurs (`wiki/sources/auteur-*.md`, skill `carnets-experts`).
- Le dossier des clients du vault (bloc D), pour la liste des noms privés.

## Interview
Lis d'abord : `wiki/sources/` (auteurs déjà sourcés), `carnets.json`, `wiki/clients/` (seulement pour lister les noms, jamais pour copier une histoire), les textes déjà publiés (pour repérer les chiffres que l'utilisateur répète souvent).

Puis demande :
1. « Quels chiffres sur toi ou ton business ont le droit d'apparaître en public ? » (exemples : année de création, prix publics, un nombre de clients que tu assumes. Chacun avec sa preuve.) Range dans `wiki/maps/chiffres-permis.txt`, un par ligne.
2. « Comment veux-tu dire ta preuve sans chiffre fragile ? » (exemple : « des centaines de clients accompagnés » plutôt qu'un nombre exact qui vieillit.) Range la phrase exacte dans `wiki/maps/regles-verite.md`.
3. « Quels auteurs as-tu le droit de citer nommément en public ? Et lesquels restent internes ? » (va dans `carnets.json`, champ `public`, et dans `auteurs.json`.)
4. « Tes clients ont-ils accepté d'être nommés quelque part ? » (par défaut : non. Un témoignage nommé demande un accord écrit, noté dans la fiche.)
5. « Une histoire inventée pour illustrer, avec un prénom fictif, c'est permis chez toi ? » (si oui : seulement si un vrai client pourrait la vivre, et jamais avec une statistique inventée.)

## Construire
1. **Poser l'outil** (Claude) : copier `outils/verite.py` dans `scripts/verite.py` du vault. `python scripts/verite.py selftest` doit imprimer `selftest OK`.
2. **Écrire les listes** (Claude) :
   - `wiki/maps/chiffres-permis.txt` (réponse 1).
   - `auteurs.json` à la racine : `{"Nom affiché": "wiki/sources/auteur-nom.md"}` pour chaque auteur citable. Les auteurs internes n'y vont pas : les citer en public sort alors une erreur.
   - `noms-prives.txt` (privé, dans `.gitignore`) : les vrais prénoms et noms des clients et de leurs proches, tirés de `wiki/clients/`. Une ligne par nom, les variantes d'orthographe comprises.
3. **Les trois commandes** que tout skill de publication lance sur le texte extrait :
   ```
   python scripts/verite.py chiffres <texte> --sources <source1> <dossier-sources> --permis wiki/maps/chiffres-permis.txt
   python scripts/verite.py attributions <texte> --auteurs auteurs.json
   python scripts/verite.py noms <texte> --liste noms-prives.txt
   ```
   Chacune sort 0 si propre, 1 avec la liste des problèmes. `--sources` reçoit la source que le texte adapte (l'article, la transcription, la réponse du carnet) : un chiffre absent de ces sources est un chiffre inventé.
4. **Écrire `wiki/maps/regles-verite.md`** (Claude), court : les trois règles, la phrase de preuve, la règle des histoires illustratives (réponse 5), et l'ordre de correction : un chiffre sans source devient qualitatif ou sort ; une citation sans fiche sort ou reçoit sa fiche ; un nom réel devient un prénom d'emprunt.
5. **Ajouter le contrôle adverse** pour les textes qui adaptent une source (Claude) : dans le skill concerné, une étape où un sous-agent en lecture seule reçoit le brouillon ET la source, et liste chaque chiffre, délai, anecdote nommée et attribution, avec « trouvé dans la source : oui ou non ». Un seul « non » bloque.
6. **Brancher** dans le board des textes (siège Vérité) et dans chaque skill de publication : les trois commandes sortent 0 avant la porte.

## Test
Sur un texte piège écrit par Claude (un pourcentage inventé, « des études montrent », un prénom de client réel) : les trois commandes sortent 1 et nomment chaque problème. Sur un vrai texte propre de l'utilisateur : les trois sortent 0.

## Pièges vécus
- **Le texte sonne juste et il est faux.** Des délais précis (« en six jours », « après 48 heures ») attribués à un auteur qui ne les avait jamais écrits. Le contrôle compare au texte source, jamais à la vraisemblance.
- **Une année ou une date fait sauter le contrôle.** Le bandeau d'un visuel portait l'année : lue comme un chiffre inventé. Mettre les chiffres légitimes dans la liste des permis, ou ne contrôler que le texte que le public lit.
- **Un chiffre de preuve qui vieillit.** Un nombre exact de clients ou d'heures, répété partout, devient faux ou fragile. Une formule assumée sans chiffre (« des centaines de personnes accompagnées ») tient dans le temps.
- **Les modèles inventent des études.** Un outil de réécriture « pour humaniser » ajoutait des études chiffrées qui n'existaient pas. Il a été retiré. Tout outil qui réécrit un texte repasse ensuite par ces contrôles.
- **Nommer un client avec son histoire.** Même avec de bonnes intentions, c'est un risque légal et une trahison de confiance. Le vrai nom reste dans le vault privé ; en public, un prénom d'emprunt et des détails modifiés.
- **Le script ne juge pas le conseil.** Il attrape les chiffres, les noms et les attributions. Le fond (le conseil est-il juste ?) reste le travail des carnets d'experts au board.

## Entretien dans le temps
- Chaque nouveau client : son nom va dans `noms-prives.txt` le jour de sa fiche.
- Chaque nouvel auteur cité : sa fiche dans `wiki/sources/` et sa ligne dans `auteurs.json`.
- Quand un faux passe malgré tout : ajouter le cas au selftest de `verite.py` (un assert de plus), pour qu'il ne repasse jamais.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (la phrase de preuve choisie). Propose ensuite `controle-voix`.
