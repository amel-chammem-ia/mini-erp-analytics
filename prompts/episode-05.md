# Épisode 5 · Devenir développeur prompt engineer

Vidéo : *Devenir développeur prompt engineer : coder avec l'IA* (Formation Prompt Engineering #5).

## 1. Le modèle de prompt de code

Les ingrédients des épisodes 1 à 4 s'appliquent aussi au code : rôle, contexte, tâche, contraintes, format.

```text
Rôle : tu es un développeur Python senior.
Contexte : le projet Mini-ERP utilise FastAPI et SQL Server (via SQLAlchemy).
Tâche : écris la fonction qui calcule le chiffre d'affaires TTC d'un mois à partir des ventes validées.
Contraintes : code typé, gestion des erreurs (mois invalide), aucune nouvelle dépendance.
Format : le code complet, puis les tests automatiques avec pytest.
```

Exemple de réponse attendue (montré dans la vidéo) :

```python
def chiffre_affaires_mois(db: Session, annee: int, mois: int) -> Decimal:
    """CA TTC des ventes validées du mois."""
    if not 1 <= mois <= 12:
        raise ValueError("Mois invalide")
    total = db.scalar(
        select(func.sum(Vente.montant_ttc))
        .where(Vente.statut == "validee",
               Vente.annee == annee,
               Vente.mois == mois))
    return total or Decimal("0")


def test_mois_invalide(db):
    with pytest.raises(ValueError):
        chiffre_affaires_mois(db, 2026, 13)
```

## 2. Prompt n° 1 du projet : le cahier des charges

```text
Tu es chef de projet logiciel.
Contexte : une PME de 20 personnes vend du matériel informatique et suit ses clients, ses ventes et son stock dans Excel.
Tâche : rédige les user stories d'un mini-ERP avec les modules clients, produits, ventes, stock, analyses et partage des tableaux de bord.
Format : un tableau avec les colonnes ID, rôle (en tant que), besoin (je veux) et critères d'acceptation. Numérote les stories US-01, US-02, etc.
```

Résultat relu, corrigé et validé : [`docs/cahier-des-charges.md`](../docs/cahier-des-charges.md).

## 3. Check-list avant d'intégrer du code généré

- [ ] La tâche était petite et précise.
- [ ] Le prompt donnait le contexte du projet (stack, conventions, fichiers concernés).
- [ ] J'ai lu et compris chaque ligne du code.
- [ ] Les tests passent, y compris les cas d'erreur.
- [ ] Aucune dépendance ni aucun secret n'a été ajouté sans raison.
- [ ] Le commit a un message clair, lié à son user story.
