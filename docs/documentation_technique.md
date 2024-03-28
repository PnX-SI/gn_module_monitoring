# Documentation technique

## SQL

## Backend

## Frontend

Une github action vérifiant le lint du frontend est réalisée .
En mode développement il est nécessaire d'effectuer avant chaque PR les commandes suivantes :

```sh
cd frontend # se placer dans le dossier frontend
nvm use # sourcer la bonne version de node
npm run format:check # vérifier l'état des fichiers frontend 
```

La sortie de la commande `npm run format:check` va renvoyer des warning en fonction des fichiers non lintés .

Si c'est le cas , alors lancer la commande : `npm run format`.
