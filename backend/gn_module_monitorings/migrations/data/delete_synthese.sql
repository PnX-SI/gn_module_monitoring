--  ###  Triggers permettant d'assurer la suppression dans la synthèse

-- Visites

DROP FUNCTION IF EXISTS gn_synthese.fct_trg_delete_synthese_visits() CASCADE;

CREATE FUNCTION gn_synthese.fct_trg_delete_synthese_visits() RETURNS trigger AS $$
BEGIN
    --Suppression des données dans la synthèse
    DELETE FROM gn_synthese.synthese WHERE unique_id_sinp = OLD.uuid_base_visit;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_delete_synthese_visits AFTER DELETE ON gn_monitoring.t_base_visits
    FOR EACH ROW EXECUTE PROCEDURE gn_synthese.fct_trg_delete_synthese_visits();


-- Observations
DROP FUNCTION IF EXISTS gn_synthese.fct_trg_delete_synthese_observations() CASCADE;

CREATE FUNCTION gn_synthese.fct_trg_delete_synthese_observations() RETURNS trigger AS $$
BEGIN
    --Suppression des données dans la synthèse
    DELETE FROM gn_synthese.synthese WHERE unique_id_sinp = OLD.uuid_observation;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_delete_synthese_observations AFTER DELETE ON gn_monitoring.t_observations
    FOR EACH ROW EXECUTE PROCEDURE gn_synthese.fct_trg_delete_synthese_observations();

