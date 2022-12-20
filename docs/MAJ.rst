=====================
Mise à jour du module
=====================

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

- Récupérez le fichier de configuration du module

::

   cp /home/`whoami`/gn_module_monitoring_old/config/conf_gn_module.toml  /home/`whoami`/gn_module_monitoring/config/conf_gn_module.toml


- Récupérez les sous-modules, recréer les liens symboliques pour la config

  - Ne jamais faire de modifications directement dans le dossier ``config/monitoring/generic``

::

   rsync -av /home/`whoami`/gn_module_monitoring_old/config/monitoring/ /home/`whoami`/gn_module_monitoring/config/monitoring/ --exclude=generic

- Recréez les liens des images des modules dans le dossier ``<geonature>/backend/static/external_assets/monitorings/``

::

   source /home/`whoami`/geonature/backend/venv/bin/activate
   geonature monitorings process_img

- Relancez la compilation en mettant à jour la configuration

::

   source <geonature>/backend/venv/bin/activate
   geonature install-gn-module gn_module_monitoring MONITORINGS
   sudo systemctl reload geonature

- Exécutez les éventuels scripts SQL de migration de la BDD indiqués dans les notes de version, correspondants aux évolutions de structure des données de la nouvelle version, dans ``/home/`whoami`/gn_module_monitoring/migrations/<choisir le(s) bon(s) en fonction des versions>``

- Recréer les vues alimentant la synthèse de GeoNature

::

   /home/`whoami`/gn_module_monitoring/data/update_views.sh /home/`whoami`/geonature
