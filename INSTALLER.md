# INSTALLER (pour Claude)

Tu viens de recevoir « Machine Claude » : la recette d'un système complet construit pendant des mois par un entrepreneur avec son Claude. Ta mission : amener la personne qui te parle à ce niveau, pour SON business, puis plus loin. Tu fais presque tout le travail. La personne fait seulement ce qui demande ses mains, ses accès ou son accord.

Lis aussi `SPEC.md` (les 4 lois de ce dossier). Ici, `<KIT>` désigne le dossier machine-claude et `<VAULT>` le dossier de travail de la personne.

**Pour un débutant**, explique chaque mot technique la première fois, en une phrase : le *vault* (le dossier où vit son second cerveau), un *commit* (une photo de sauvegarde de ce dossier), un *hook* (un petit contrôle automatique que Claude Code lance tout seul), le *frontmatter* (les quelques lignes d'étiquettes en haut d'une page), un *skill* (une recette que Claude sait suivre).

## 1. Trouver le vault
- Si tu as été ouvert dans `<KIT>` lui-même, demande où vit (ou doit vivre) son second cerveau. Propose `Documents/Cerveau` s'il n'a rien. Demande-lui ensuite de rouvrir Claude Code dans `<VAULT>` et de redire « installe » (donne-lui la phrase exacte à copier, avec le chemin du KIT).
- Ne travaille jamais à l'intérieur de `<KIT>` : il doit rester propre pour les mises à jour.

## 2. Les outils de base (vérifie toi-même, installe avec son accord)
| Outil | Vérifier | Installer sous Windows | Installer sur Mac |
|:-|:-|:-|:-|
| git | `git --version` | `winget install Git.Git` | `xcode-select --install` |
| Python 3.9+ | `python --version` (Mac : `python3`) | `winget install Python.Python.3.12` | `brew install python` ou python.org |
| Node LTS | `node --version` | `winget install OpenJS.NodeJS.LTS` | `brew install node` ou nodejs.org |
Après une installation par winget, il faut parfois fermer et rouvrir Claude Code pour que la commande soit trouvée : dis-le simplement.

## 3. Sauvegarder avant tout
- Si `<VAULT>` n'est pas un dépôt git : `git init`, puis `git config core.autocrlf false` (évite des centaines d'avertissements inutiles sous Windows), puis un premier commit de l'état actuel.
- Si un `CLAUDE.md` existe, copie-le en `CLAUDE.avant-machine.md`. Ne supprime et n'écrase jamais rien sans sauvegarde.

## 4. Première interview (10 minutes, en une fois)
Lis d'abord ce qui existe (CLAUDE.md, mémoire, wiki) pour ne pas redemander. Puis demande seulement ce qui manque :
1. Son prénom, et comment tu dois parler de toi : au masculin, au féminin ou de façon neutre.
2. Son activité en une phrase et depuis quand.
3. Son niveau avec l'informatique (débutant, à l'aise, technique) : adapte le détail de tes explications.
4. Le temps qu'il ou elle peut donner par semaine.
5. Ce qui l'agace le plus chez son Claude aujourd'hui.
6. Son système (Windows, Mac, Linux) : vérifie-le toi-même.
Range les réponses dans `wiki/maps/moi.md` (crée la page à l'étape 5). Elles serviront à toutes les briques : aucune brique ne les redemande.

## 5. Le squelette du vault
Lance `python <KIT>/.claude/skills/architecture-vault/outils/creer-vault.py <VAULT> --dossiers principes,clients,sources,contenu,strategie,business,maps` (il crée raw/, wiki/, outputs/, index.md, log.md et n'écrase rien). Écris `wiki/maps/moi.md` avec les réponses de l'interview, un frontmatter et des liens vers [[index]], [[parcours]] et [[routage]].

## 6. Installer le cœur
Remplis `CLAUDE.modele.md` : `{{PRENOM}}`, `{{ACTIVITE}}`, `{{NIVEAU}}`, `{{TEMPS}}`, et `{{LIGNE_GENRE}}` par UNE de ces lignes :
- masculin : « Tu es un homme. En français, tu parles de toi au masculin, toujours : « je suis prêt », « je suis sûr », « je suis allé vérifier ». »
- féminin : « Tu es une femme. En français, tu parles de toi au féminin, toujours : « je suis prête », « je suis sûre », « je suis allée vérifier ». »
- neutre : « Tu parles de toi de façon neutre, sans accord marqué : « c'est prêt », « j'ai vérifié ». »
Puis fusionne-le dans `<VAULT>/CLAUDE.md`. Garde ce qui existe et qui est utile. Une contradiction : tu la notes et tu poses la question, tu ne choisis pas seul. Le `CLAUDE.md` reste sous 260 lignes.

## 7. Copier les pièces (jamais les dossiers `__pycache__`)
| Depuis `<KIT>` | Vers `<VAULT>` |
|:-|:-|
| `.claude/skills/*` | `.claude/skills/` (un skill du même nom existe déjà : compare, garde le meilleur, dis-le) |
| `.claude/commands/*` | `.claude/commands/` (même règle) |
| `.claude/hooks/*` | `.claude/hooks/` |
| `.claude/agents/*` | `.claude/agents/` |
| `outils/cerveau.py`, `outils/verifier-installation.py`, `outils/planche.py` | `scripts/` |
| `parcours/blueprint.md`, `parcours/bloc-*.md` | `wiki/maps/machine/` (remplace chaque AAAA-MM-JJ par la date du jour) |
| `parcours/parcours-modele.md` | `wiki/maps/parcours.md` (remplace chaque AAAA-MM-JJ par la date du jour) |
| `parcours/routage-modele.md` | `wiki/maps/routage.md` (même chose pour les dates) |
Les autres fichiers de `outils/` (tâches planifiées, notifications, gardien, rapport du matin) se copient seulement quand le bloc F les demande. `outils/generer-parcours.py` sert au mainteneur du kit : ne le copie pas.
Ajoute les pages copiées dans `index.md` (une ligne chacune, section Machine).

**Brancher les hooks.** Si `.claude/settings.json` n'existe pas, copie `.claude/settings.hooks.json` sous ce nom. Sinon, fusionne par un petit script Python (lire les deux JSON, ajouter chaque entrée de `hooks` absente, réécrire), jamais à la main, puis vérifie que le fichier se relit (`python -c "import json;json.load(open('.claude/settings.json', encoding='utf-8'))"`). Les hooks prennent effet à la prochaine session : dis-lui de fermer et rouvrir Claude Code à la fin de l'installation.

## 8. Tester
Lance `python scripts/verifier-installation.py`. Il doit afficher PASS. Chaque ÉCHEC dit quoi corriger : corrige et relance jusqu'à PASS. Le premier lancement de la recherche peut télécharger un petit modèle de langue (quelques minutes, une seule fois) : préviens-le.

## 9. L'audit (étape 0)
Compare `<VAULT>` au blueprint brique par brique. Dans `wiki/maps/parcours.md`, chaque ligne est désignée par le NOM de son skill : ce qui existe et marche est ✅, ce qui existe à moitié est 🟡 avec ce qui manque, le reste ❌. Ne refais jamais ce qui marche déjà.

## 10. Le rapport
Format TL;DR / AUTO / TOI / ALERTE : ce qui est en place, les 3 trous les plus importants et LA prochaine brique (20 minutes maximum). Commit « Machine installée ». Note la version du kit (date en haut de `CHANGELOG.md`) dans `wiki/maps/parcours.md`. Donne-lui la phrase magique : « On continue le parcours. »

## Mettre à jour depuis une nouvelle version du KIT
Quand il ou elle dit « mets à jour la machine » avec un nouveau dossier : lis `CHANGELOG.md` depuis la version notée dans `wiki/maps/parcours.md`, applique seulement les changements, ne touche jamais à ce qui a été personnalisé (compare avant de remplacer), ajoute au parcours les nouvelles briques, relance `python scripts/verifier-installation.py`, puis note la nouvelle version.
