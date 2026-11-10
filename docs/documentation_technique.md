# Documentation technique

## Backend

### Lancer les tests avec `pytest`

Pour lancer les tests, il vous faut :

- Une instance de développement GeoNature
- Une base de données GeoNature vierge, issue d'une installation récente et sans données ajoutées

> [!NOTE]
>
> Pour vous aider, plusieurs images de base de données vierges de GeoNature sont disponibles sur https://github.com/PnX-SI/geonature_db.
>
> ```sh
> # Pour lancer une BDD de GeoNature avec (Occhab, Occtax, Validation, >Monitoring, Dashboard et Export)
> docker run -d \
>    --name geonature-db \
>    --rm \
>    -p 5432:5432 \
>    ghcr.io/pnx-si/geonature-db-extra:latest
>
> # Appliquer les dernières révisions
> geonature db autoupgrade && geonature upgrade-modules-db
> ```

Pour lancer les tests, mettez vous dans le dossier de GeoNature.

```sh
source backend/venv/bin/activate
pytest <chemin_vers_dossier_gn_module_monitoring>
```

## Frontend

Une GitHub Action vérifie le formatage du code frontend. En développement, il est donc nécessaire de lancer les commandes suivantes avant chaque PR :

```sh
cd frontend           # se placer dans le dossier frontend
nvm use               # utiliser la bonne version de node
npm run format:check  # vérifier le formatage des fichiers frontend
```

La commande `npm run format:check` renvoie des avertissements pour les fichiers mal formatés. Si c'est le cas, lancer :

```sh
npm run format
```
