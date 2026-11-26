"""Crée le premier compte administrateur (épisode 10).

    docker compose exec api python -m app.creer_admin admin@votre-entreprise.fr "Prénom Nom"

Le mot de passe est demandé au clavier (deux fois) et n'apparaît ni à l'écran, ni dans
l'historique du terminal, ni dans un fichier. Les autres comptes se créent ensuite par l'API.
"""
import argparse
import getpass
import sys

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_engine
from .models import Utilisateur
from .schemas import UtilisateurCreation
from .securite import hacher_mot_de_passe


def creer_administrateur(session: Session, email: str, nom: str, mot_de_passe: str) -> Utilisateur:
    """Valide les données avec le même schéma que l'API, puis enregistre le compte."""
    donnees = UtilisateurCreation(email=email, nom=nom, role="administrateur", mot_de_passe=mot_de_passe)
    if session.scalar(select(Utilisateur.id).where(Utilisateur.email == donnees.email)) is not None:
        raise ValueError("Un compte utilise déjà cette adresse e-mail")
    admin = Utilisateur(email=donnees.email, nom=donnees.nom, role=donnees.role,
                        mot_de_passe_hache=hacher_mot_de_passe(donnees.mot_de_passe))
    session.add(admin)
    session.commit()
    return admin


def main() -> int:
    parser = argparse.ArgumentParser(description="Crée un compte administrateur.")
    parser.add_argument("email")
    parser.add_argument("nom")
    args = parser.parse_args()

    mot_de_passe = getpass.getpass("Mot de passe (12 caractères minimum) : ")
    if getpass.getpass("Confirmez le mot de passe : ") != mot_de_passe:
        print("Les deux saisies ne correspondent pas.", file=sys.stderr)
        return 1
    try:
        with Session(get_engine()) as session:
            admin = creer_administrateur(session, args.email, args.nom, mot_de_passe)
    except ValidationError as erreur:
        for detail in erreur.errors():
            print(f"{'.'.join(map(str, detail['loc']))} : {detail['msg']}", file=sys.stderr)
        return 1
    except ValueError as erreur:
        print(erreur, file=sys.stderr)
        return 1
    print(f"Administrateur créé : {admin.email} (id {admin.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
