# Mise à jour du module

Avant la mise à jour
====================

- Si vous ne l'avez pas encore fait, copier l'éventuelle configuration du module dans le dossier centralisé de GeoNature (depuis sa version 2.12) :

  ``` sh
  cp ~/gn_module_monitoring/config/conf_gn_module.toml  ~/geonature/config/monitorings_config.toml
  ```

- Si vous ne l'avez pas encore fait, copier les configurations des sous-modules dans le dossier `media` de geonature
  - attention à bien reproduire la commande :
    - source : `gn_module_monitoring_old/config/monitoring` (sans `s`)
    * destination : `~/geonature/config/monitorings` (avec `s`)

  ```sh
  cp -R ~/gn_module_monitoring_old/config/monitoring/* ~/geonature/backend/media/monitorings
  rm -R ~/geonature/backend/media/monitorings/generic
  ```

  Les chemins sont à adapter si l'emplacement du dossier `media` de GeoNature à été modifié.

Mise à jour du module
=====================

* Téléchargez la nouvelle version du module

  ```sh
  wget https://github.com/PnX-SI/gn_module_monitoring/archive/X.Y.Z.zip
  unzip X.Y.Z.zip
  rm X.Y.Z.zip
  ```

* Renommez l'ancien et le nouveau répertoire

  ```sh
  mv ~/gn_module_monitoring ~/gn_module_monitoring_old
  mv ~/gn_module_monitoring-X.Y.Z ~/gn_module_monitoring
  ```

* Lancez la mise à jour du module

  ```sh
  source ~/geonature/backend/venv/bin/activate
  geonature install-gn-module gn_module_monitoring MONITORINGS
  sudo systemctl reload geonature
  ```
  
* Recréer les vues alimentant la synthèse de GeoNature

  ```sh
  geonature monitorings process_csv
  ```
