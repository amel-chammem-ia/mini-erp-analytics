"""Sécurité : hachage des mots de passe, jetons de connexion, limite de tentatives (épisode 10).

Ce module ne dépend ni de FastAPI ni de la base : il se teste seul.

- Les mots de passe sont hachés avec scrypt (bibliothèque standard), un sel aléatoire par
  compte et des paramètres coûteux. On ne stocke jamais un mot de passe en clair, et on ne
  peut pas le retrouver à partir de son empreinte.
- Le jeton de connexion est un JWT signé (HS256) avec JWT_SECRET, lu dans le fichier .env.
  Il ne contient que l'identifiant de l'utilisateur : le rôle est relu en base à chaque requête,
  pour qu'un changement de rôle ou une désactivation prenne effet immédiatement.
"""
import base64
import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from functools import cache

import jwt

# Hachage des mots de passe ------------------------------------------------
# Paramètres recommandés par l'OWASP pour scrypt : N = 2^17, r = 8, p = 1 (128 Mio, ~0,4 s).
# Ils sont écrits dans chaque empreinte : on pourra les durcir sans casser les anciens comptes.
SCRYPT_N = 2**17
SCRYPT_R = 8
SCRYPT_P = 1
TAILLE_SEL = 16
TAILLE_CLE = 32
MEMOIRE_MAX = 2**28  # 256 Mio : scrypt refuse de dépasser cette limite


def _b64(octets: bytes) -> str:
    return base64.urlsafe_b64encode(octets).decode().rstrip("=")


def _deb64(texte: str) -> bytes:
    return base64.urlsafe_b64decode(texte + "=" * (-len(texte) % 4))


def _scrypt(mot_de_passe: str, sel: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(mot_de_passe.encode(), salt=sel, n=n, r=r, p=p,
                          maxmem=MEMOIRE_MAX, dklen=TAILLE_CLE)


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Renvoie une empreinte autoportante : scrypt$N$r$p$sel$cle."""
    sel = secrets.token_bytes(TAILLE_SEL)
    cle = _scrypt(mot_de_passe, sel, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64(sel)}${_b64(cle)}"


def verifier_mot_de_passe(mot_de_passe: str, empreinte: str) -> bool:
    """True si le mot de passe correspond. Une empreinte illisible ne correspond jamais."""
    try:
        algo, n, r, p, sel, cle = empreinte.split("$")
        if algo != "scrypt":
            return False
        attendu = _deb64(cle)
        calcule = _scrypt(mot_de_passe, _deb64(sel), int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    # Comparaison en temps constant : la durée ne révèle pas combien d'octets sont justes.
    return hmac.compare_digest(calcule, attendu)


@cache
def _empreinte_factice() -> str:
    return hacher_mot_de_passe(secrets.token_urlsafe(16))


def simuler_verification() -> None:
    """Pour un e-mail inconnu, on fait le même calcul : le temps de réponse ne trahit pas
    l'existence du compte."""
    verifier_mot_de_passe("mot de passe factice", _empreinte_factice())


# Jetons de connexion (JWT) -------------------------------------------------
ALGORITHME = "HS256"
DUREE_JETON = timedelta(minutes=30)
LONGUEUR_MIN_SECRET = 32


class JetonInvalide(Exception):
    """Jeton absent, expiré, falsifié ou mal formé."""


def verifier_secret(secret: str) -> None:
    if len(secret) < LONGUEUR_MIN_SECRET:
        raise RuntimeError(
            f"JWT_SECRET doit faire au moins {LONGUEUR_MIN_SECRET} caractères. "
            "Générez-en un : python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )


def creer_jeton(utilisateur_id: int, secret: str, maintenant: datetime | None = None) -> str:
    verifier_secret(secret)
    maintenant = maintenant or datetime.now(timezone.utc)
    charge = {"sub": str(utilisateur_id), "iat": maintenant, "exp": maintenant + DUREE_JETON}
    return jwt.encode(charge, secret, algorithm=ALGORITHME)


def lire_jeton(jeton: str, secret: str) -> int:
    """Renvoie l'identifiant de l'utilisateur, ou lève JetonInvalide."""
    verifier_secret(secret)
    try:
        # algorithms est imposé : un jeton signé avec un autre algorithme (ou "none") est refusé.
        charge = jwt.decode(jeton, secret, algorithms=[ALGORITHME],
                            options={"require": ["sub", "iat", "exp"]})
        return int(charge["sub"])
    except (jwt.PyJWTError, ValueError) as erreur:
        raise JetonInvalide(str(erreur)) from None


# Limite des tentatives de connexion ---------------------------------------
class LimiteurTentatives:
    """Bloque un e-mail après trop d'échecs sur une fenêtre glissante (attaque par force brute).

    En mémoire : suffisant pour un seul processus d'API. À plusieurs serveurs, on stockerait
    les compteurs dans une base partagée.
    """

    def __init__(self, max_echecs: int = 5, fenetre_secondes: int = 15 * 60):
        self.max_echecs = max_echecs
        self.fenetre = fenetre_secondes
        self._echecs: dict[str, deque[float]] = defaultdict(deque)
        self._verrou = threading.Lock()

    def _purger(self, cle: str, maintenant: float) -> deque[float]:
        echecs = self._echecs[cle]
        while echecs and maintenant - echecs[0] >= self.fenetre:
            echecs.popleft()
        return echecs

    def est_bloque(self, cle: str, maintenant: float | None = None) -> bool:
        maintenant = time.monotonic() if maintenant is None else maintenant
        with self._verrou:
            return len(self._purger(cle, maintenant)) >= self.max_echecs

    def noter_echec(self, cle: str, maintenant: float | None = None) -> None:
        maintenant = time.monotonic() if maintenant is None else maintenant
        with self._verrou:
            self._purger(cle, maintenant).append(maintenant)

    def reinitialiser(self, cle: str | None = None) -> None:
        with self._verrou:
            if cle is None:
                self._echecs.clear()
            else:
                self._echecs.pop(cle, None)
