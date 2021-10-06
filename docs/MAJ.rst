=====================
Mise à jour du module
=====================

Gestion du code avec git
========================

( un autre façon de gérer les mises à jour du module (au moins au niveau du code) est
- à l'installation
  - récupérer le code du module avec ``git clone https://github.com/PnX-SI/gn_module_monitoring/``
  - passer au tag voulu : ``git co 0.2.6``
- à la mise à jour
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


- Récupérez les sous-modules, recréer les liens symboliques pour la config
  - Ne jamais faire de modifications directement dans generic

::

   rsync -av /home/`whoami`/gn_module_monitoring_old/config/monitoring/ /home/`whoami`/gn_module_monitoring/config/monitoring/ --exclude=generic


- Recréez les liens des images des modules dans le dossier backend/static/monitorings/assets

::

   source /home/`whoami`/geonature/backend/venv/bin/activate
   geonature monitorings process_img

  - si la version de GeoNature est antérieure à 2.7.5

::
   source /home/`whoami`/geonature/backend/venv/bin/activate
   export FLASK_APP=geonature
   flask monitorings process_img


- Relancez la compilation en mettant à jour la configuration

::

   source /home/`whoami`/geonature/backend/venv/bin/activate
   geonature update_module_configuration MONITORINGS

- Si GeoNature est supérieur à 2.7.0 jouer le script `data/patch_geonature_2.7.0.sql` pour retirer les champs `meta_create_date` et `meta_update_date`

- Exécutez les éventuels scripts SQL de migration de la BDD, correspondant aux évolutions de structure des données de la nouvelle version, dans ``/home/`whoami`/gn_module_monitoring/migrations/<choisir le(s) bon(s) en fonction des versions>``

- Recréer les vues alimentant la synthèse de GeoNature

::

   /home/`whoami`/gn_module_monitoring/data/update_views.sh /home/`whoami`/geonature
