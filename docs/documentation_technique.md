# Documentation technique

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
