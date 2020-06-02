

-- Fonction import dans la synthese

CREATE OR REPLACE FUNCTION gn_synthese.import_json_row(
	datain json
)
RETURNS boolean AS
$BODY$
  DECLARE
    insert_columns text;
    select_columns text;
    update_columns text;

  BEGIN

    -- Import des données dans une table temporaire pour faciliter le traitement
	DROP TABLE IF EXISTS tmp_process_import;
    CREATE TEMP TABLE tmp_process_import (
        id_synthese int,
        datain json,
        action char(1)
    );
    INSERT INTO tmp_process_import (datain)
    SELECT datain;

-- ############ TEST

	-- colonne unique_id_sinp exists
	IF EXISTS (
        SELECT 1 FROM json_object_keys(datain) column_name WHERE column_name =  'unique_id_sinp'
    ) IS FALSE THEN
        RAISE NOTICE 'Column unique_id_sinp is mandatory';
        RETURN FALSE;
	END IF ;

-- ############ mapping colonnes

    WITH import_col AS (
		SELECT json_object_keys(datain) AS column_name
	), synt_col AS (
        SELECT column_name, column_default, CASE WHEN data_type = 'USER-DEFINED' THEN NULL ELSE data_type END as data_type
        FROM information_schema.columns
        WHERE table_schema || '.' || table_name = 'gn_synthese.synthese'
    )
    SELECT
        string_agg(s.column_name, ',')  as insert_columns,
        string_agg(
            CASE
                WHEN NOT column_default IS NULL THEN 'COALESCE((datain->>''' || i.column_name  || ''')' || COALESCE('::' || data_type, '') || ', ' || column_default || ') as ' || i.column_name
            ELSE '(datain->>''' || i.column_name  || ''')' || COALESCE('::' || data_type, '')
            END, ','
        ) as select_columns ,
        string_agg(
            s.column_name || '=' || CASE
                WHEN NOT column_default IS NULL THEN 'COALESCE((datain->>''' || i.column_name  || ''')' || COALESCE('::' || data_type, '') || ', ' || column_default || ') '
            ELSE '(datain->>''' || i.column_name  || ''')' || COALESCE('::' || data_type, '')
            END
        , ',')
    INTO insert_columns, select_columns, update_columns
    FROM synt_col s
    JOIN import_col i
    ON i.column_name = s.column_name;

    -- ############# IMPORT DATA
   	IF EXISTS (
        SELECT 1
        FROM   gn_synthese.synthese
        WHERE  unique_id_sinp = (datain->>'unique_id_sinp')::uuid
    ) IS TRUE THEN
		-- Update
		EXECUTE ' WITH i_row AS (
            UPDATE gn_synthese.synthese s SET ' || update_columns ||
            ' FROM  tmp_process_import
            WHERE s.unique_id_sinp =  (datain->>''unique_id_sinp'')::uuid
            RETURNING s.id_synthese, s.unique_id_sinp
            )
            UPDATE tmp_process_import d SET id_synthese = i_row.id_synthese
            FROM i_row
            WHERE unique_id_sinp = i_row.unique_id_sinp
            ' ;
    ELSE
		-- Insert
       EXECUTE 'WITH i_row AS (
            INSERT INTO gn_synthese.synthese ( ' || insert_columns || ')
            SELECT ' || select_columns ||
            ' FROM tmp_process_import
            RETURNING id_synthese, unique_id_sinp
            )
            UPDATE tmp_process_import d SET id_synthese = i_row.id_synthese
            FROM i_row
            WHERE unique_id_sinp = i_row.unique_id_sinp
            ' ;
    END IF;

	-- Import des cor_observers
    DELETE FROM gn_synthese.cor_observer_synthese
    USING tmp_process_import
	WHERE cor_observer_synthese.id_synthese = tmp_process_import.id_synthese;

    INSERT INTO gn_synthese.cor_observer_synthese (id_synthese, id_role)
    SELECT DISTINCT id_synthese, (json_array_elements(t.datain->'ids_observers'))::text::int
    FROM tmp_process_import t;

	RETURN TRUE;
  END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

