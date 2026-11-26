# Connexion et droits par rôle

Mise en place à l'épisode 10 (cahier des charges : US-09 et exigence de sécurité).

## Qui a le droit de faire quoi

✅ autorisé · ❌ refusé (`403`)

| Droit | Commercial | Vendeur | Magasinier | Manager | Dirigeant | Administrateur |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `clients:lire` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| `clients:ecrire` | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `clients:supprimer` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `produits:lire` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `produits:ecrire` | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| `ventes:lire` (ép. 11) | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| `ventes:ecrire` (ép. 11) | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| `ventes:valider` (ép. 11) | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| `stock:lire` (ép. 12) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `stock:ecrire` (ép. 12) | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| `statistiques:lire` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `utilisateurs:gerer` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

La matrice vit dans un seul fichier, [`backend/app/droits.py`](../backend/app/droits.py), et chaque route déclare le droit qu'elle exige :

```python
@router.post("", dependencies=[autoriser("clients:ecrire")])
```

Un nom de droit mal écrit fait échouer le démarrage de l'API : l'erreur ne peut pas passer en production.

## Comment marche la connexion

1. `POST /api/auth/connexion` avec l'e-mail et le mot de passe.
2. L'API compare le mot de passe à son **empreinte** enregistrée en base et renvoie un **jeton signé**, valable 30 minutes.
3. L'interface envoie ce jeton à chaque requête : `Authorization: Bearer <jeton>`.
4. À chaque requête, l'API vérifie la signature et l'expiration du jeton, **relit le compte en base** (rôle, compte actif), puis contrôle le droit de la route.

Le jeton ne contient que l'identifiant de l'utilisateur. Le rôle est relu en base à chaque requête : un changement de rôle ou une désactivation s'applique immédiatement, sans attendre l'expiration du jeton.

## Les règles de sécurité

| Règle | Comment |
|---|---|
| Aucun mot de passe en clair | Empreinte **scrypt** (bibliothèque standard Python), sel aléatoire de 16 octets par compte, paramètres OWASP (N = 2¹⁷, r = 8, p = 1). Format : `scrypt$N$r$p$sel$empreinte` |
| Mots de passe solides | 12 caractères minimum, 128 maximum |
| Aucun secret dans le code | Le jeton est signé avec `JWT_SECRET`, lu dans le fichier `.env` (jamais envoyé sur GitHub). L'API refuse de démarrer sans un secret d'au moins 32 caractères |
| Erreurs qui ne révèlent rien | Même réponse « E-mail ou mot de passe incorrect » que l'e-mail existe ou non, et même durée de calcul (vérification factice pour un e-mail inconnu) |
| Force brute | 5 échecs en 15 minutes sur un e-mail : `429`, même avec le bon mot de passe |
| Jetons falsifiés | Algorithme imposé (HS256) : un jeton modifié, signé avec un autre secret ou non signé (`alg: none`) est refusé |
| Pas de verrouillage accidentel | Un administrateur ne peut ni se désactiver ni se retirer son propre rôle |

## 401 ou 403 ?

| Code | Signification | Exemple |
|---|---|---|
| `401` | On ne sait pas qui vous êtes | pas de jeton, jeton expiré ou falsifié, compte désactivé |
| `403` | On sait qui vous êtes, mais votre rôle ne le permet pas | un vendeur qui crée un produit |

## Mise en route

1. Générez un secret et collez-le dans `.env` :

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   ```text
   JWT_SECRET=le-secret-généré
   ```

2. Relancez : `docker compose up --build`. La table `utilisateurs` est créée par `db-init`.

3. Créez le premier administrateur. Le mot de passe est demandé au clavier : il n'apparaît ni à l'écran, ni dans l'historique, ni dans un fichier.

   ```bash
   docker compose exec api python -m app.creer_admin admin@votre-entreprise.fr "Prénom Nom"
   ```

4. Les autres comptes se créent avec `POST /api/utilisateurs` (administrateur uniquement).

## Limites connues

- Le compteur d'échecs est en mémoire : il repart à zéro au redémarrage et n'est pas partagé entre plusieurs serveurs. Suffisant pour un seul conteneur ; à revoir à la mise en production (épisode 19).
- Le blocage après 5 échecs vise un e-mail : quelqu'un peut bloquer un compte pendant 15 minutes en se trompant exprès. C'est le compromis habituel face à la force brute.
- Pas de déconnexion côté serveur : un jeton reste valable jusqu'à son expiration (30 minutes). Désactiver le compte le coupe immédiatement.
