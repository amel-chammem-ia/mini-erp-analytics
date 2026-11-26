"""Qui a le droit de faire quoi : la matrice des droits par rôle (épisode 10).

Une seule source de vérité, lisible par un humain et vérifiée par les tests.
Les rôles viennent du cahier des charges (section 3). Les droits des ventes et du stock
sont déjà décidés ici ; leurs routes arrivent aux épisodes 11 et 12.
"""

ROLES = ("commercial", "vendeur", "magasinier", "manager", "dirigeant", "administrateur")

TOUS = frozenset(ROLES)

DROITS: dict[str, frozenset[str]] = {
    # Clients
    "clients:lire": frozenset({"commercial", "vendeur", "manager", "dirigeant", "administrateur"}),
    "clients:ecrire": frozenset({"commercial", "administrateur"}),
    "clients:supprimer": frozenset({"administrateur"}),
    # Produits : tout le monde consulte le catalogue, le magasinier le tient à jour
    "produits:lire": TOUS,
    "produits:ecrire": frozenset({"magasinier", "administrateur"}),
    # Ventes (épisode 11)
    "ventes:lire": frozenset({"commercial", "vendeur", "manager", "dirigeant", "administrateur"}),
    "ventes:ecrire": frozenset({"vendeur", "administrateur"}),
    "ventes:valider": frozenset({"vendeur", "administrateur"}),
    # Stock (épisode 12)
    "stock:lire": frozenset({"vendeur", "magasinier", "manager", "dirigeant", "administrateur"}),
    "stock:ecrire": frozenset({"magasinier", "administrateur"}),
    # Analyses
    "statistiques:lire": frozenset({"manager", "dirigeant", "administrateur"}),
    # Comptes
    "utilisateurs:gerer": frozenset({"administrateur"}),
}


def verifier_droit(droit: str) -> None:
    """Une faute de frappe dans un nom de droit doit casser au démarrage, pas en production."""
    if droit not in DROITS:
        raise KeyError(f"Droit inconnu : {droit!r}")


def a_le_droit(role: str, droit: str) -> bool:
    verifier_droit(droit)
    return role in DROITS[droit]


def droits_du_role(role: str) -> list[str]:
    """La liste des droits d'un rôle, triée : renvoyée par /api/auth/moi pour l'interface."""
    return sorted(droit for droit, roles in DROITS.items() if role in roles)
