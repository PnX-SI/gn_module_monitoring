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

- Récupérez les sous-modules

::

   cp -r /home/`whoami`/gn_module_monitoring_old/contrib  /home/`whoami`/gn_module_monitoring/contrib

- Relancez la compilation en mettant à jour la configuration

::

   cd /home/`whoami`/geonature/backend
   source venv/bin/activate
   geonature update_module_configuration MONITORINGS
