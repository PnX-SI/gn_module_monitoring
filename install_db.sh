#!/bin/bash

GN_PATH="$1"

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"


. $GN_PATH/config/settings.ini

LOG_FILE="$GN_PATH/var/log/install_db_gn_module_suivi.log"

echo "Create schema gn_suivi_generique ..." > $LOG_FILE
echo "--------------------" &>> $LOG_FILE
echo "" &>> $LOG_FILE

export PGPASSWORD=$user_pg_pass;psql -h $db_host -U $user_pg -d $db_name -f $SCRIPTPATH/data/schema_suivis_generique.sql &>> $LOG_FILE
