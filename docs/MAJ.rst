=====================
Mise à jour du module
=====================


- Téléchargez la nouvelle version du module

::

   wget https://github.com/PnX-SI/gn_module_monitoring/archive/X.Y.Z.zip
   unzip X.Y.Z.zip
   rm X.Y.Z.zip


- Renommez l'ancien et le nouveau répertoire

::

   mv /home/`whoami`/gn_module_monitoring /home/`whoami`/gn_module_monitoring_old
   mv /home/`whoami`/gn_module_monitoring-X.Y.Z /home/`whoami`/gn_module_monitoring


- Rapatriez le fichier de configuration du module

::

   cp /home/`whoami`/gn_module_monitoring_old/config/conf_gn_module.toml  /home/`whoami`/gn_module_monitoring/config/conf_gn_module.toml

- Récupérez les sous-modules, recréer les liens symboliques pour la config

::

   cp -r /home/`whoami`/gn_module_monitoring_old/contrib/*  /home/`whoami`/gn_module_monitoring/contrib
   ln -s /home/`whoami`/gn_module_monitoring/contrib/* /home/`whoami`/gn_module_monitoring/config/monitoring/.


- Recréez les liens des images des modules dans le dossier backend/static/monitorings/assets

::
   cd /home/`whoami`/geonature/backend
   source venv/bin/activate
   export FLASK_APP=/home/`whoami`/geonature/backend/geonature/app.py
   flask monitorings process_img


- Relancez la compilation en mettant à jour la configuration

::

   cd /home/`whoami`/geonature/backend
   source venv/bin/activate
   geonature update_module_configuration MONITORINGS


- Exécutez les éventuels scripts SQL de migration de la BDD, correspondant aux évolutions de structure des données de la nouvelle version, dans ``/home/`whoami`/gn_module_monitoring/migrations/<choisir le(s) bon(s) en fonction des versions>``

- Recréer les vues alimentant la synthèse de GeoNature

::

   /home/`whoami`/gn_module_monitoring/data/update_views.sh /home/`whoami`/geonature
