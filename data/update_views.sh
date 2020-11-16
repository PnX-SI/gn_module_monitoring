# script pour mettre à jour les vues (dev)

gn_path="$1"

module_code_in="$2"

scriptpath="$( cd "$(dirname "$0")" ; pwd -P )"

. ${gn_path}/config/settings.ini 

log_file="${gn_path}/var/log/update_views.log"

echo "Add views for synthese in schema gn_monitoring ..." > ${log_file}
echo "--------------------" &>> ${log_file}
echo "" &>> ${log_file}

# boucle sur les fichiers synthese des sous-modules


for nom_fichier in $(ls ${scriptpath}/../config/monitoring/*/synthese.sql)
    do
        [ -f "${nom_fichier}" ] || continue
        module_code=${nom_fichier%/*}
        module_code=${module_code##*/}
        [ -n "${module_code_in}" ] && [ "${module_code_in}" != "${module_code}" ] && continue
        echo "process synthese for module ${module_code}" "${nom_fichier}"
        export PGPASSWORD=${user_pg_pass};psql -h ${db_host} -U ${user_pg} -d ${db_name} -f ${nom_fichier} --set=module_code=${module_code} &>> ${log_file}
    done

    cat ${log_file} | grep ERR
