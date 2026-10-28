---
name: youtube-systeme
description: "Installe la semaine YouTube complète : banque d'idées vidéo mesurée, 3 miniatures, titres, description, plan de tournage, sortie et lecture des chiffres. Utiliser quand l'utilisateur dit « prépare mes vidéos », « on tourne quoi cette semaine », « lance ma chaîne YouTube ». Pas pour le texte du script (utiliser script-video) ni le montage (utiliser montage-video-code)."
---
# Système YouTube

## Pourquoi
La vidéo longue est devenue la pièce mère du système d'origine : tout le reste en dérive (Shorts, carrousels, posts, articles). Au départ, les sujets étaient choisis sans mesure et presque aucune vue ne venait de la recherche. La semaine type a réglé ça : Claude mesure la demande, prépare tout, l'entrepreneur valide en quelques minutes, tourne en lot, et Claude s'occupe du reste. La cadence a été posée en plancher tenable (deux à trois vidéos par semaine, tournées en lot) avec un bilan prévu après une douzaine de vidéos.

## Prérequis
- `banque-idees`, `accroches`, `script-video`, `tournage`, `montage-video-code`, `distribution-api`.
- Une chaîne YouTube. Option : vidIQ (payant) pour la mesure des mots-clés, un générateur d'image pour les miniatures (`images-de-marque`).
- Bloc C (`board-textes`, carnet expert pour le fond, carnet stratégie YouTube si l'utilisateur en monte un).

## Interview
Lis d'abord : la banque, `wiki/maps/machine-contenu.md`, `wiki/maps/moi.md`, les chiffres de sa chaîne s'il en a. Puis demande :
1. « Combien de vidéos longues par semaine, même une mauvaise semaine ? Et quelle durée ? » Range dans `wiki/maps/youtube.md`, section « Cadence ». Propose deux formats si utile : une vidéo phare plus longue et des réponses plus courtes à une vraie question.
2. « Quel jour peux-tu tourner en lot ? » Range dans « Semaine type ».
3. « Où veux-tu envoyer les gens après la vidéo ? » (ressource gratuite, appel, liste email). Un seul appel principal.
4. « Acceptes-tu d'être à l'image sur tes miniatures ? » Range dans « Miniatures ».

## Construire
1. **Mesurer la demande** (Claude, 15 min). Pour chaque idée de la banque : relève les suggestions de saisie YouTube et Google (gratuites), regarde le top 10 de la requête, note les trous (requête forte, réponses faibles). Option vidIQ sur les finalistes. Range dans `outputs/youtube/banque-videos.md` avec une colonne « demande ».
2. **Choisir et vérifier** (Claude, 10 min). Garde les idées qui collent au client idéal et ont une demande. Vérifie le fond au carnet expert (bloc C). L'utilisateur dit oui ou change (15 minutes de son temps au plus).
3. **Le paquet de chaque vidéo** (Claude, 20 min). Dans `outputs/youtube/<slug>/` : 3 titres de travail, 3 idées de miniature de familles différentes (au moins une change l'idée elle-même), la description (réponse en 2 lignes, chapitres, liens), le plan de tournage. Le script vient de `script-video`.
4. **Les miniatures** (Claude, 15 min). Règles qui ont tenu : 5 mots au plus sur 2 lignes, lisible à 120 px de large, un personnage principal évident, l'expression a une cause visible, moins d'éléments, le texte complète le titre sans le répéter. Prépare la photo avant le tournage (pose, regard, tenue). Génère par `images-de-marque` et note chaque miniature sur une grille avant de la montrer.
5. **Après le tournage** (Claude). Montage (`montage-video-code`), transcription locale, titres et miniatures finaux tirés de ce qu'il a vraiment dit, contrôle (le mot-clé est dit dans la première minute), puis `distribution-api` et `decoupe-shorts`.
6. **Les gestes qu'aucune API ne fait** (l'utilisateur, 5 min). Guide-le dans YouTube Studio : écran de fin (Contenu, la vidéo, Écran de fin, « Importer depuis une vidéo » dès la deuxième), épingler le commentaire, charger les 3 miniatures dans « Tester et comparer ». Écris ces gestes dans une feuille du jour J à cocher.
7. **Lire** (Claude). À 2 jours : taux de clic et rétention à 30 secondes. À 7 jours : durée moyenne vue, clics vers l'appel, gagnant du test. Inscris tout au registre de `mesure-et-apprentissage`.

## Test
Une vidéo est sortie avec ses 3 miniatures en test, sa feuille du jour J cochée, et ses chiffres à 2 et 7 jours sont dans le registre.

## Pièges vécus
- Choisir les sujets à l'intuition : presque aucune vue venue de la recherche. Mesure d'abord.
- Trois miniatures qui ne changeaient que la couleur : le test n'apprend rien. Au moins une variante change l'idée.
- Un visage inconnu seul en miniature sur une petite chaîne n'attire personne : il réagit à quelque chose de visible (un message, un objet, une scène).
- Un logo en filigrane sur les miniatures, jugé moche et inutile : retiré.
- Un plan trop ambitieux (une vidéo par jour) : gel et rien ne sort. Un plancher tenu bat un pic abandonné.
- Exporter en résolution plus basse que le tournage : la vidéo perd sa netteté. Exporte dans la résolution filmée.

## Entretien dans le temps
Bilan après une douzaine de vidéos : les 3 meilleures et les 3 pires au taux de clic, la rétention à 30 s, la part de recherche, les clics vers l'appel. Trois changements au plus pour la série suivante. Ce qui a raté ne se refait pas à l'identique.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (cadence, jour de tournage). Propose ensuite `script-video`.
