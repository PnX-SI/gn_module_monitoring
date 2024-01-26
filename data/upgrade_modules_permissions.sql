-- ######### Mise à jour des permissions des modules

-- Doit être réalisé après avoir lancé la commande :
--      `geonature monitorings update_module_available_permissions`

/*
Etapes : 
 0 - Vérification que les objets MONITORING_XXX ont bien été définis pour les modules
 1 - Transfert des permissions de l'objet ALL vers MONITORING_XXX
 2 - Suppression des permissions available pour l'objet ALL
 3 - Suppression des permissions qui ne sont pas dans les permissions available
*/



DO $$  
DECLARE 
BEGIN 
    -- Etape 0 : 
    -- CHECK command update_module_available_permissions disponibles 
    --  c-a-d qu'il y a autre chose que l'objet all comme permissions disponibles
   IF EXISTS(WITH ap AS (
		SELECT o.code_object,o.id_object, tpa.id_module
		FROM gn_permissions.t_permissions_available AS tpa
		JOIN gn_permissions.t_objects AS o
		ON o.id_object = tpa.id_object AND NOT code_object = 'ALL'
		JOIN gn_commons.t_modules AS tm
		ON tm.id_module = tpa.id_module AND tm.type = 'monitoring_module'
		JOIN gn_permissions.bib_actions AS ba
		ON tpa.id_action = ba.id_action
		WHERE NOT (code_object = 'MONITORINGS_MODULES' AND ba.code_action = 'U')
	) 
		SELECT tm.id_module , tm.module_label , count(DISTINCT ap.code_object), array_agg(ap.code_object)
		FROM gn_commons.t_modules tm 
		LEFT OUTER JOIN ap 
		ON ap.id_module = tm.id_module 
		WHERE tm.type = 'monitoring_module'
		GROUP BY tm.id_module , tm.module_label
		HAVING count(DISTINCT ap.code_object) = 0
	)
    THEN 
        RAISE EXCEPTION 'La commande "geonature monitorings update_module_available_permissions" doit être lancée avant l''utilisation de ce script';
    ELSE

        -- Etape 1 : 
        --  Mise à jour des permissions existantes vers les sous objets
        --  Création des permissions des sous-objets à partir des permissions contenus dans l'objet ALL
        WITH ap AS (
            SELECT o.code_object,o.id_object, tpa.id_module
            FROM gn_permissions.t_permissions_available AS tpa
            JOIN gn_permissions.t_objects AS o
            ON o.id_object = tpa.id_object AND NOT code_object = 'ALL'
            JOIN gn_commons.t_modules AS tm
            ON tm.id_module = tpa.id_module AND tm.type = 'monitoring_module'
            JOIN gn_permissions.bib_actions AS ba
            ON tpa.id_action = ba.id_action
            WHERE NOT (code_object = 'MONITORINGS_MODULES' AND ba.code_action = 'U')
        ), ep AS (
                SELECT id_role, id_action, tp.id_module , tp.id_object, scope_value, sensitivity_filter
                FROM gn_permissions.t_permissions AS tp
                JOIN gn_permissions.t_objects AS o
                ON o.id_object = tp.id_object  
                JOIN gn_commons.t_modules AS tm
                ON tm.id_module = tp.id_module AND tm.type = 'monitoring_module'
        ), new_p AS (
            SELECT DISTINCT ep.id_role, ep.id_action, ep.id_module, ap.id_object, ep.scope_value, ep.sensitivity_filter
            FROM ep
            JOIN ap
            ON ep.id_module = ap.id_module
            LEFT OUTER JOIN  gn_permissions.t_permissions AS p
            ON p.id_role = ep.id_role
            AND  p.id_action = ep.id_action
            AND  p.id_module = ep.id_module
            AND  p.id_object = ap.id_object
            WHERE p.id_permission IS NULL
        )
        INSERT INTO gn_permissions.t_permissions
        (id_role, id_action, id_module, id_object, scope_value, sensitivity_filter)
        SELECT id_role, id_action, id_module, id_object, scope_value, sensitivity_filter
        FROM new_p;
            
         
        -- Etape 2 :   
        --  Suppression des objects ALL des permissions disponibles (t_permissions_available)
        WITH to_del AS (
            SELECT tp.*
            FROM gn_permissions.t_permissions_available AS tp
            JOIN gn_commons.t_modules AS tm
            ON tm.id_module = tp.id_module AND tm.type = 'monitoring_module'
            JOIN gn_permissions.t_objects AS o
            ON o.id_object = tp.id_object AND code_object = 'ALL'
        )
        DELETE FROM gn_permissions.t_permissions_available AS tp
        USING to_del td
        WHERE  
            tp.id_module = td.id_module
            AND tp.id_object = td.id_object
            AND tp.id_action = td.id_action
            AND tp."label" = td."label"
            AND tp.scope_filter = td.scope_filter
            AND tp.sensitivity_filter = td.sensitivity_filter;


        -- Etape 3 :   
        -- Suppression des permissions qui ne sont pas dans les permissions disponibles (t_permissions_available)
        WITH to_del AS (
            SELECT tp.id_permission
            FROM gn_permissions.t_permissions AS tp
            JOIN gn_commons.t_modules AS tm
            ON tm.id_module = tp.id_module AND tm.type = 'monitoring_module'
            LEFT OUTER JOIN gn_permissions.t_permissions_available AS ta
            ON tp.id_action = ta.id_action
            AND tp.id_module = ta.id_module
            AND tp.id_object = ta.id_object
            WHERE ta.id_module  IS NULL
        )
        DELETE FROM  gn_permissions.t_permissions AS tp
        WHERE tp.id_permission IN (SELECT id_permission FROM to_del);

    END IF;
END $$
 