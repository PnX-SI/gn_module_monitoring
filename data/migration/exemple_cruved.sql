INSERT INTO gn_permissions.t_objects (code_object, description_object)
VALUES
('GNM_SITES', 'Permissions sur les sites'),
('GNM_VISITES', 'Permissions sur les visites'),
('GNM_OBSERVATIONS', 'Permissions sur les observation'),
('GNM_GRP_SITES', 'Permissions sur les groupes de sites')
;


INSERT INTO gn_permissions.cor_object_module (id_object, id_module)
SELECT id_object, id_module
FROM (
SELECT id_module
FROM gn_commons.t_modules tm WHERE module_code = 'cheveches'
) AS m, gn_permissions.t_objects o
WHERE o.code_object ILIKE 'GNM_%';
