# A jouer depuis <geonature_install ??>

MODULE_DIR=$"${0%/*}"
FLASKDIR="${0%/*/*}"/..
log_file=$FLASKDIR/var/log/monitorings.log

. $FLASKDIR/config/settings.ini
export PGPASSWORD=$user_pg_pass;

echo " Installation du schema pour le module MONITORINGS
" &> $log_file
psql -h $db_host -U $user_pg -d $db_name -f ${MODULE_DIR}/data/monitoring.sql &>> $log_file
psql -h $db_host -U $user_pg -d $db_name -f ${MODULE_DIR}/data/delete_synthese.sql &>> $log_file
