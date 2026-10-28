---
name: skills-marketing
description: "Installe le pack public de skills marketing coreyhaines31/marketingskills (offre, page de vente, emails, réseaux, tests A/B, psychologie, comité marketing...) et écrit leur contexte produit commun à partir du vault, puis branche le filtre de voix et le board sur tout ce qu'ils produisent. Utiliser quand l'utilisateur dit « installe les skills marketing », « aide-moi sur mon offre ou ma page de vente », « il me faut des conseils marketing sérieux ». Pas pour juger un texte fini (utiliser board-textes)."
---
# Les skills marketing

## Pourquoi
Écrire de zéro une méthode pour chaque sujet marketing coûte des semaines. Le pack public de Corey Haines (dépôt GitHub coreyhaines31/marketingskills) en fournit des dizaines, solides et à jour : offre, page de vente, emails, réseaux, tests, prix. Dans le système d'origine, ils servent pour tout conseil marketing, en plus du board. Leur sortie brute a pourtant une voix d'agence américaine : elle passe toujours par la voix et le board de l'utilisateur avant d'être utilisée.

## Prérequis
- Node.js (pour `npx`). Vérifier : `node --version`.
- L'entretien fondateur (bloc D) : client idéal, offres, preuves, voix. Le contexte produit en est tiré.
- `controle-voix` et `board-textes` (filtres de sortie).
- Coût : gratuit (dépôt public).

## Interview
Lis d'abord : la fiche client idéal, la page des offres, le guide de voix, les preuves permises (`wiki/maps/regles-verite.md`), et `.agents/` s'il existe déjà.

Puis demande :
1. « Sur quoi veux-tu de l'aide marketing en premier : ton offre, ta page de vente, tes emails, tes réseaux, autre chose ? » (décide quels skills montrer d'abord.)
2. « Tes canaux actuels, et ceux que tu ne veux pas toucher ? » (va dans le contexte produit.)
3. « Y a-t-il des tactiques que tu refuses, même si elles marchent ? » (exemples : fausse rareté, compte à rebours truqué. Va dans le contexte produit, section Interdits.)

## Construire
1. **Installer** (Claude), depuis la racine du vault :
   ```
   npx skills add coreyhaines31/marketingskills
   ```
   L'outil propose une liste : tout prendre, ou les skills de la réponse 1. Il copie les skills dans `.agents/skills/` et les relie à `.claude/skills/`. Vérifier : un dossier `.claude/skills/copywriting/` (ou un des skills choisis) existe et contient un `SKILL.md`.
   - Windows : si les liens symboliques échouent (droits), relancer en terminal administrateur, ou copier les dossiers de `.agents/skills/` vers `.claude/skills/`.
2. **Trouver le nom du fichier de contexte** (Claude). Selon la version du pack, les skills lisent `.agents/product-marketing.md` ou l'ancien `.agents/product-marketing-context.md`. Lancer `grep -rho "product-marketing[a-z-]*\.md" .claude/skills/copywriting/SKILL.md` (ou un autre skill installé) pour voir le nom attendu.
3. **Écrire le contexte produit** (Claude) sous ce nom, depuis le vault, sans rien inventer :
   ```
   # Contexte marketing (lu par les skills marketing)
   ## Produit            ce que l'utilisateur vend, en deux phrases
   ## Client idéal       qui, sa situation, ses mots exacts (3 à 5 verbatims pseudonymisés)
   ## Offres et parcours chaque offre, son prix public, l'étape suivante pour le client
   ## Preuves            uniquement les preuves permises (wiki/maps/regles-verite.md)
   ## Voix et interdits  tutoiement ou vouvoiement, mots bannis, tactiques refusées (réponse 3)
   ## Canaux             ceux utilisés, ceux exclus
   ```
   Montrer le fichier à l'utilisateur : « Est-ce que c'est toi ? » Corriger.
4. **Brancher le filtre de sortie** (Claude), dans `CLAUDE.md` : « Toute sortie d'un skill marketing est matière première. Avant de la montrer comme texte final : réécriture dans la voix de l'utilisateur, `lint_voix.py`, contrôles de vérité, puis board des textes si elle part chez un client. Une recommandation de stratégie non triviale se double d'une question au carnet d'expert concerné (routage des carnets). »
5. **Ajouter au routage des intentions** (bloc B) les déclencheurs utiles (« mon offre », « ma page de vente », « une séquence d'emails », « teste deux versions ») vers le skill du pack correspondant.

## Test
Demande à Claude une amélioration de l'offre ou d'une page réelle de l'utilisateur. Réussi si : le skill du pack se déclenche, sa proposition cite le contexte produit (le vrai client idéal, la vraie offre), et le texte final sort 0 au lint de voix.

## Pièges vécus
- **La voix d'agence.** La sortie brute ressemble à une page de vente américaine, avec des tournures repérées comme écrites par une IA. D'où le filtre obligatoire de l'étape 4.
- **Le contexte périmé.** Les skills lisent le fichier de contexte à chaque fois : une offre changée sans mise à jour donne des conseils faux. Le relire à chaque changement d'offre ou de prix.
- **Le nom du fichier change selon la version.** Un contexte écrit sous l'ancien nom n'est pas lu par les skills récents. D'où l'étape 2.
- **Tactique prouvée, version honnête.** Le pack propose parfois de la rareté ou de l'urgence. On garde le mécanisme dans sa version vraie (une vraie limite de places, une vraie date), jamais la version truquée.
- **Trop de skills, aucun usage.** Installer des dizaines de skills sans routage, c'est ne jamais les voir se déclencher. L'étape 5 les rend utiles.

## Entretien dans le temps
- Tous les trois mois : `npx skills add coreyhaines31/marketingskills` à nouveau pour mettre à jour (ou la commande de mise à jour que l'outil indique), puis relire le contexte produit.
- Le contexte produit se met à jour le jour où une offre, un prix ou une preuve change.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (les skills du pack les plus utilisés). Le bloc C est complet : propose le bloc suivant du parcours.
