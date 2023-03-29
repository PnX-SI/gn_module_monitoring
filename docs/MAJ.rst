=====================
Mise à jour du module
=====================

Avant la mise à jour
====================


::

   cp ~/gn_module_monitoring_old/config/conf_gn_module.toml  ~/geonature/config/monitorings_config.toml


- Si vous ne l'avez pas encore fait, copier les configuration des modules dans le dossier ``media`` de geonature
    - attention à bien reproduire la commande:
        - source : ``gn_module_monitoring_old/config/monitoring`` (sans ``s``)
        - destination : ``~/geonature/config/monitorings`` (avec ``s``)

::
   cp -R ~/gn_module_monitoring_old/config/monitoring ~/geonature/backend/media/monitorings
   rm -R geonature/config/monitorings/generic


- à adapter si l'emplacement du dossier media à été modifié

Gestion des fichiers avec git
=============================

Si vous souhaitez installer et mettre à jour le module avec git :

- à l'installation

  - récupérer le code du module avec ``git clone https://github.com/PnX-SI/gn_module_monitoring/``
  - passer au tag voulu : ``git co 0.2.6``

- à la mise à jour

  - ``git pull``
  - passer au tag voulu : ``git co 0.2.7``


Méthode classique
=================

- Téléchargez la nouvelle version du module

::

   wget https://github.com/PnX-SI/gn_module_monitoring/archive/X.Y.Z.zip
   unzip X.Y.Z.zip
   rm X.Y.Z.zip

- Renommez l'ancien et le nouveau répertoire

::

   mv /home/`whoami`/gn_module_monitoring /home/`whoami`/gn_module_monitoring_old
   mv /home/`whoami`/gn_module_monitoring-X.Y.Z /home/`whoami`/gn_module_monitoring


- Lancez la mise à jour du module

::

   source ~/geonature/backend/venv/bin/activate
   geonature install-gn-module gn_module_monitoring MONITORINGS
   sudo systemctl reload geonature

- Recréer les vues alimentant la synthèse de GeoNature

::

   geonature monitorings process_csv