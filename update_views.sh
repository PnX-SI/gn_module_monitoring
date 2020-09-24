# script pour mettre à jour les vues (dev)

GN_PATH="$1"

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

. $GN_PATH/config/settings.ini

LOG_FILE="$GN_PATH/var/log/update_views.log"

echo "Add tables in schema gn_monitoring ..." > $LOG_FILE
echo "--------------------" &>> $LOG_FILE
echo "" &>> $LOG_FILE

export PGPASSWORD=$user_pg_pass;psql -h $db_host -U $user_pg -d $db_name -f $SCRIPTPATH/data/vues.sql &>> $LOG_FILE


# boucle sur les fichiers synthese des sous-modules

for nom_fichier in $(ls $SCRIPTPATH/config/monitoring/*/synthese.sql)
do
[ -f "$nom_fichier" ] || continue
echo nom_fichier $SCRIPTPATH$nom_fichier
export PGPASSWORD=$user_pg_pass;psql -h $db_host -U $user_pg -d $db_name -f $nom_fichier &>> $LOG_FILE
done

cat $LOG_FILE | grep ERROR
