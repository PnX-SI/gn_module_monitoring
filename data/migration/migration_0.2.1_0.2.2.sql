-- Ajout contrainte sur la table des objets de permission
-- Devrait être dans GN2
-- TODO supprimer ces deux lignes une fois présentes dans GN2
ALTER TABLE gn_permissions.t_objects DROP CONSTRAINT IF EXISTS unique_t_objects;
ALTER TABLE gn_permissions.t_objects ADD CONSTRAINT unique_t_objects UNIQUE (code_object);


INSERT INTO gn_permissions.t_objects (code_object, description_object)
VALUES
('GNM_SITES', 'Permissions sur les sites'),
('GNM_VISITES', 'Permissions sur les visites'),
('GNM_OBSERVATIONS', 'Permissions sur les observation'),
('GNM_GRP_SITES', 'Permissions sur les groupes de sites')
ON CONFLICT(code_object) DO NOTHING;
;
