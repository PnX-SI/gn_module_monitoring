"""
Crée (ou met à jour) les comptes utilisés par la recette E2E : un compte par worker Playwright,
`e2e.worker1` … `e2e.workerN`, pour que chaque worker fasse varier ses propres permissions.

Chaque compte est :
- rattaché à l'organisme `--organisme` (le même que le rôle « collègue » GN_ROLE_SAME_ORG,
  pour que le scope 2 « mon organisme » soit testable) ;
- membre du groupe `--group` (accès à l'application GeoNature) : ce groupe ne doit pas donner
  de droits sur les sous-modules E2E ;
- ajouté à la liste d'observateurs `--observers-list` des sous-modules E2E.

Les rôles propriétaires des données « collègue » et « autre organisme » (`--data-owners`) sont
aussi ajoutés à cette liste : sinon les observateurs de leurs visites ne sont pas proposés et le
formulaire d'édition de ces visites reste invalide.

Passe par les modèles pypnusershub, comme `geonature user add` (qui ne gère ni l'organisme ni
les listes). À lancer avec l'environnement virtuel de GeoNature :

    python e2e/scripts/create_test_users.py --count 4 --password e2e-password
"""

import argparse

import sqlalchemy as sa
from geonature.app import create_app
from pypnusershub.db.models import User, UserList
from pypnusershub.env import db


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--count", type=int, default=4, help="nombre de comptes (= workers)")
    parser.add_argument("--password", default="e2e-password")
    parser.add_argument("--organisme", type=int, default=-1, help="id_organisme des comptes")
    parser.add_argument("--group", default="Grp_en_poste", help="groupe donnant l'accès à GeoNature")
    parser.add_argument("--observers-list", type=int, default=1, help="id_liste des observateurs")
    parser.add_argument(
        "--data-owners",
        default="4,9999",
        help="id_role « collègue » et « autre organisme » (GN_ROLE_SAME_ORG, GN_ROLE_OTHER_ORG)",
    )
    args = parser.parse_args()

    with create_app().app_context():
        group = db.session.execute(
            sa.select(User).filter_by(groupe=True, nom_role=args.group)
        ).scalar_one()
        observers = db.session.get(UserList, args.observers_list)
        for i in range(1, args.count + 1):
            identifiant = f"e2e.worker{i}"
            user = db.session.execute(
                sa.select(User).filter_by(identifiant=identifiant)
            ).scalar_one_or_none()
            if user is None:
                user = User(identifiant=identifiant, prenom_role="E2E", nom_role=f"Worker {i}")
                db.session.add(user)
            user.password = args.password
            # pas de valeur par défaut côté modèle : un rôle non actif est absent des listes
            # d'observateurs (vue v_userslist_forall_menu)
            user.active = True
            user.id_organisme = args.organisme
            if group not in user.groups:
                user.groups.append(group)
            if observers is not None and user not in observers.users:
                observers.users.append(user)
            db.session.flush()
            print(f"{identifiant} : id_role={user.id_role}")
        for id_role in [int(i) for i in args.data_owners.split(",") if i]:
            owner = db.session.get(User, id_role)
            if observers is not None and owner not in observers.users:
                observers.users.append(owner)
        db.session.commit()


if __name__ == "__main__":
    main()
