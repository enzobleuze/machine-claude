---
description: "Note une somme encaissée. Utiliser quand l'utilisateur dit « j'ai vendu », « X m'a payé », « /vente montant prénom »."
---
# /vente : noter une vente

Arguments : `montant prénom` (et le produit s'il le dit).

1. Ajoute une ligne à `wiki/finances/ventes.md` : `| AAAA-MM-JJ | montant | prénom | produit |` (crée la page avec un tableau si elle manque).
2. Mets à jour le total du mois et l'objectif « actuel » dans `wiki/strategie/plan.md`.
3. Si le Cockpit est installé (`scripts/cockpit/cockpit_build.py` existe), note aussi la vente pour lui : `python -X utf8 scripts/cockpit/cockpit_build.py vente <montant> <prénom> --offre <produit>` (le Cockpit lit `outputs/cockpit/ventes.jsonl`).
4. Mets à jour la fiche du client dans `wiki/clients/` (achat, date).
5. Réponds en une ligne : « Noté : X € de prénom. Mois : total / cible. »

Ces pages sont privées : elles ne sortent jamais de la machine.
