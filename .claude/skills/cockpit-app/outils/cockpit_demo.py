#!/usr/bin/env python3
"""Cockpit : un faux vault complet, aux noms inventés, pour les tests et le mode démo (cockpit_serveur.py --demo).

faux_vault(dossier, today) écrit le vault et rend (vault, secrets). Les dates sont calculées depuis `today` :
la démo a toujours l'air d'aujourd'hui. Aucun vrai nom, aucun vrai chiffre, aucune clé.
"""
import datetime as dt
import json
from pathlib import Path
from string import Template

PLAN = Template("""---
title: "Plan unique"
type: strategie
cap:
  libelle: "6 000 € par mois"
  mensuel: 6000
  echeance: $cap
jalons:
  - {echeance: $jalon, mensuel: 2500}
trimestre:
  nom: "Ce trimestre"
  fin: $trim
  objectifs:
    - {titre: "Ventes signées", cible: 6, actuel: 1, unite: "ventes"}
    - {titre: "Appels tenus", cible: 20, actuel: null, unite: "appels"}  # pas encore compté
mois:
  cible: 2000
semaine:
  debut: $lun_iso
  chose: "Finir la page de vente"
---

# Plan unique

## Semaine du $lun au $dim
- [x] Lundi $lun, toi 20 min : relire l'offre
- [ ] Mardi $mar, toi 15 min : valider la page
- [ ] Claude, sans ton temps : écrire les relances

## Feuille de route
### Étape 1 : vendre (fin visée le $fin1)
Preuve de fin : trois ventes notées dans le Cockpit.
- [x] Écrire l'offre
- [ ] **PROCHAINE** Page de vente : écrire le premier jet
- [ ] Envoyer la page à cinq anciens clients

### Étape 2 : remplir l'agenda (fin visée le $fin2)
- [ ] Ouvrir les créneaux d'appel
- [ ] Publier deux fois par semaine

## Chantiers
### Site : nouvelle page d'accueil
- [x] Choisir la photo
- [ ] Écrire le titre
""")

FICHE = Template("""---
title: "$nom"
type: $type
statut: $statut
offre: "$offre"
date_debut: $debut
valeur_contrat: $valeur
paye: $paye
dernier_echange: $dernier
attend_reponse: $attend
prochain_pas: "$pas"
source: "vidéo"
tags: [client]
---
# $nom

## Situation de départ
$situation

## Objectifs
$objectifs

## Ce qui compte pour lui
Aime marcher le dimanche.

## Journal
$journal

## Appels
$appels

## Paiements et contrat
- Contrat : $contrat

## Coordonnées
$coord
""")

ECHELLE = """# Échelle d'offres

| Marche | Prix | Ce qu'elle contient | Marche suivante | Quand la proposer | Où on la montre |
|-|-|-|-|-|-|
| Guide gratuit | 0 € | Le guide en PDF | Atelier du mois | Juste après le guide | partout |
| Atelier du mois | 29 € par mois | Un atelier en ligne chaque mois | Accompagnement 3 mois | Après deux ateliers suivis | partout |
| Accompagnement 3 mois | 900 € | Douze séances et un suivi par message | Séance privée | À la fin des trois mois | sur appel |
| Séance privée | 150 € | Une séance de deux heures | | Quand une question bloque | en coulisse |
"""

SCRIPT_APPEL = """# Script d'appel

## Sécurité
Si la personne dit qu'elle est en danger, tu arrêtes la vente et tu l'orientes vers les secours de son pays.

## Accueil
> Bonjour [prénom], merci d'avoir pris ce temps.

Consigne : souris, ralentis, laisse un silence.

> Tu me racontes ce qui t'a fait réserver cet appel ?

## Situation
> Depuis quand ça dure ?

> Qu'as-tu déjà essayé ?

## Proposition
> Voilà ce que je te propose : trois mois ensemble, douze séances.

## Fin
> On se fixe la première séance maintenant ?
"""

OBJECTIONS = """# Objections et réponses

## C'est trop cher
> Je comprends. Combien te coûte la situation chaque mois où rien ne change ?

## Je dois réfléchir
> Bien sûr. À quoi veux-tu réfléchir exactement ?
"""

TACHES = """# Tâches

## En cours
- [ ] Préparer l'atelier du mois
- [ ] Refaire la page de vente

## À faire
- [ ] Envoyer la facture de janvier $retard
- [ ] Appeler l'imprimeur $bientot

## Fait
- [x] Choisir le thème de l'atelier
"""

ICS = Template("""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:atelier
DTSTART:${lun}T180000
DTEND:${lun}T193000
RRULE:FREQ=WEEKLY;BYDAY=TU
SUMMARY:Atelier du mardi
END:VEVENT
BEGIN:VEVENT
UID:appel-sam
DTSTART:${demain}T100000
DTEND:${demain}T104500
SUMMARY:Appel découverte
END:VEVENT
BEGIN:VEVENT
UID:conge
DTSTART;VALUE=DATE:${conge}
DTEND;VALUE=DATE:${conge2}
SUMMARY:Journée sans écran
END:VEVENT
END:VCALENDAR
""")


def _jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def faux_vault(dossier, today=None):
    today = today or dt.date.today()
    v, j = Path(dossier), lambda n: (today + dt.timedelta(days=n)).isoformat()
    lun = today - dt.timedelta(days=today.weekday())
    dm = lambda d: d.strftime("%d/%m")
    for d in ("wiki/strategie", "wiki/clients", "wiki/maps", "wiki/business", "wiki/scripts", "outputs/cron-logs", "secrets"):
        (v / d).mkdir(parents=True, exist_ok=True)
    (v / "wiki/strategie/plan.md").write_text(PLAN.substitute(
        cap=j(1000), jalon=j(170), trim=j(80), lun_iso=lun.isoformat(), lun=dm(lun), mar=dm(lun + dt.timedelta(days=1)),
        dim=dm(lun + dt.timedelta(days=6)), fin1=dm(today + dt.timedelta(days=24)), fin2=dm(today + dt.timedelta(days=60))), encoding="utf-8")
    gens = [
        dict(id="alex-test", nom="Alex Test", type="client", statut="actif", offre="Accompagnement 3 mois", debut=j(-40), valeur=900, paye=450,
             dernier=j(-5), attend=j(-5), pas="Lui envoyer le lien de la séance", situation="Il disait : « je cours partout et je n'avance pas ».",
             objectifs="- Tenir trois matinées calmes par semaine", journal="- **{}** (message) : demande s'il peut décaler la séance".format(j(-5)),
             appels="- **{}** : appel de lancement".format(j(-38)), contrat="signé", coord="alex@example.com"),
        dict(id="sam-essai", nom="Sam Essai", type="lead", statut="prospect", offre="", debut=j(-3), valeur="null", paye="null",
             dernier=j(0), attend=j(0), pas="", situation="", objectifs="", journal="- **{}** (formulaire) : veut en savoir plus".format(j(0)),
             appels="", contrat="", coord=""),
        dict(id="kim-ancien", nom="Kim Ancien", type="client", statut="ancien", offre="Atelier du mois", debut=j(-500), valeur=29, paye=29,
             dernier=j(-400), attend="null", pas="", situation="", objectifs="- Reprendre le sport", journal="", appels="", contrat="absent",
             coord="kim@example.com"),
        dict(id="lou-exemple", nom="Lou Exemple", type="client", statut="actif", offre="Atelier du mois", debut=j(-260), valeur=29, paye=29,
             dernier=j(-200), attend="null", pas="Proposer l'accompagnement", situation="", objectifs="- Dormir mieux",
             journal="- **{}** (appel) : contente de l'atelier".format(j(-200)), appels="", contrat="signé", coord="lou@example.com"),
        dict(id="noa-demo", nom="Noa Démo", type="lead", statut="perdu", offre="", debut=j(-90), valeur="null", paye="null",
             dernier=j(-80), attend="null", pas="", situation="", objectifs="", journal="", appels="", contrat="", coord=""),
    ]
    for g in gens:
        (v / "wiki/clients" / (g.pop("id") + ".md")).write_text(FICHE.substitute(**g), encoding="utf-8")
    (v / "wiki/clients/_index.md").write_text("# Index des clients\n", encoding="utf-8")
    (v / "wiki/clients/cassee.md").write_text("---\ntype client\n---\n", encoding="utf-8")
    (v / "wiki/business/echelle-offres.md").write_text(ECHELLE, encoding="utf-8")
    (v / "wiki/scripts/script-appel.md").write_text(SCRIPT_APPEL, encoding="utf-8")
    (v / "wiki/scripts/objections-reponses.md").write_text(OBJECTIONS, encoding="utf-8")
    (v / "wiki/maps/taches.md").write_text(Template(TACHES).substitute(retard=j(-2), bientot=j(3)), encoding="utf-8")
    (v / "wiki/maps/parking.md").write_text("# Parking à idées\n\n## À trier\n- {} [appel] Un atelier sur le sommeil\n\n## Contenu\n"
                                            "- {} : Une vidéo sur les matinées calmes\n".format(j(-1), j(-9)), encoding="utf-8")
    out = v / "outputs/cockpit"
    _jsonl(out / "ventes.jsonl", [{"date": j(-1), "montant": 450.0, "qui": "Alex Test", "offre": "Accompagnement 3 mois"},
                                  {"date": j(-45), "montant": 29.0, "qui": "Lou Exemple"}])
    _jsonl(out / "historique.jsonl", [{"date": j(-14), "mois": j(-14)[:7], "encaisse": None, "etapes": {"Étape 1 : vendre": 0}},
                                      {"date": j(-7), "mois": j(-7)[:7], "encaisse": None, "etapes": {"Étape 1 : vendre": 0}},
                                      {"date": j(-3), "mois": j(-3)[:7], "encaisse": None, "etapes": {"Étape 1 : vendre": 1}}])
    _jsonl(out / "reseaux/releves.jsonl", [{"date": j(-35), "reseau": "instagram", "abonnes": 1000, "source": "manuel"},
                                           {"date": j(-8), "reseau": "instagram", "abonnes": 1100, "source": "manuel"},
                                           {"date": j(-1), "reseau": "instagram", "abonnes": 1180, "source": "claude"},
                                           {"date": j(-31), "reseau": "youtube", "abonnes": 200, "source": "manuel"},
                                           {"date": j(-10), "reseau": "youtube", "abonnes": 260, "source": "manuel"}])
    _jsonl(out / "reseaux/publications.jsonl", [{"date": j(-n), "reseau": "instagram", "titre": t, "vues": vues, "url": None}
                                               for n, t, vues in ((2, "La matinée calme", 4200), (6, "Trois erreurs du soir", 900),
                                                                  (9, "Mon carnet", 1100), (14, "Une question de Sam", 1000), (20, "Le réveil", 300))])
    _jsonl(out / "reseaux/commentaires.jsonl", [{"id": "c1", "reseau": "instagram", "auteur": "un abonné", "texte": "Ça marche aussi le week-end ?",
                                                 "date": j(-1) + "T20:14", "publication": "La matinée calme", "url": None},
                                                {"id": "c2", "reseau": "youtube", "auteur": "une abonnée", "texte": "Merci, j'ai essayé hier.",
                                                 "date": j(-2) + "T09:02", "publication": "Le réveil", "url": None}])
    for slug_, board in (("premiere-video", "## Verdict : VERT\n"), ("deuxieme-video", None)):
        d = v / "outputs/youtube" / slug_
        d.mkdir(parents=True, exist_ok=True)
        (d / "script.md").write_text("# {}\n\nBonjour. Ce soir, on parle des matinées calmes.\n".format(slug_.replace("-", " ").capitalize()), encoding="utf-8")
        if board:
            (d / "board.md").write_text("# Board\n" + board, encoding="utf-8")
    c = v / "outputs/courts/scripts"
    c.mkdir(parents=True, exist_ok=True)
    (c / "1-une-scene.md").write_text("# Une scène du soir\n\nIl est tard, le téléphone brille encore.\n", encoding="utf-8")
    (c / "1-une-scene.board.md").write_text("## Verdict : À TRANCHER\n", encoding="utf-8")
    (c / "2-le-carnet.md").write_text("# Le carnet\n\nJ'écris trois lignes avant de dormir.\n", encoding="utf-8")
    (c / "2-le-carnet.board.md").write_text("## Verdict : VERT\n", encoding="utf-8")
    (v / "outputs/cron-logs/resume-{}.log".format(j(0))).write_text(
        "07:02:11 [warn] Sauvegarde : le dépôt n'a pas été poussé | relance la sauvegarde\n07:05:00 [info] Rapport du matin écrit | rien à signaler\n",
        encoding="utf-8")
    ics = v / "agenda.ics"
    ics.write_text(ICS.substitute(lun=lun.strftime("%Y%m%d"), demain=(today + dt.timedelta(days=1)).strftime("%Y%m%d"),
                                  conge=(today + dt.timedelta(days=9)).strftime("%Y%m%d"), conge2=(today + dt.timedelta(days=10)).strftime("%Y%m%d")),
                   encoding="utf-8")
    (v / "secrets/agenda.env").write_text("AGENDA_ICAL_URL={}\n".format(ics.resolve().as_uri()), encoding="utf-8")
    return v, v / "secrets"
