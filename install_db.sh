# A jouer depuis <geonature_install ??>

GEONATURE_DIR=$1
MODULE_DIR=$(readlink -e "${0%/*}")/

if [ -z "$GEONATURE_DIR" ]; then
    echo "$0 : Veuillez précisier l'emplacement de GeoNature (install_db.sh <chemin vers GeoNature>)"
    exit 1
fi

if [ "$(id -u)" == "0" ]; then
   echo "This script must not be run as root" 1>&2
   exit 1
fi

. ${GEONATURE_DIR}/config/settings.ini

log_file=$FLASKDIR/var/log/monitorings.log

. $FLASKDIR/config/settings.ini
export PGPASSWORD=$user_pg_pass;

echo " Installation du schema pour le module MONITORINGS
" &> $log_file
psql -h $db_host -U $user_pg -d $db_name -f ${MODULE_DIR}/data/monitoring.sql &>> $log_file
psql -h $db_host -U $user_pg -d $db_name -f ${MODULE_DIR}/data/delete_synthese.sql &>> $log_file
