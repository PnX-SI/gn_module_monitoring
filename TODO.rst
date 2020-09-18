====
TODO
====

* date du jour par defaut
* doc à fond
* base_type_code requis

impt
====

* serializer et populate propre (avec schéma comme dans occtax??, dans serializable.from_dict ???
* passer par object et plus par id ??
* config custom plus en base ?? (comme avec les id_dataset ??)
* valider et valider visites -> disabled et un seul qui tourne
* bug JDD visite
* bug post observation
* help dans dynamic form

petites modifications
=====================

* placer les médias au niveau des proriétés & toujours possible de 
* créer un composant booleen
* Créer un tri par défaut en config
* Pouvoir choisir les colonnes à afficher dans le tableau
* Ameliorer perf récupération de la geom en geojson (ajout fct Utils-Flask-SQLA-Geo)
* Afficher plus d'info sur les composants non valides d'un formulaire (Messages, etc...) Surtout pour la carte quand il faut renseignerla géomtrie (site)
* Faire un composant générique repris par les autres composant (pour ne pas redéfinir certains Inputs, Outputs (bEdit, obj) et services)
* compliquer le module de test avec un nombre d'invidus pour les observations (ou nb_min nb_max) et refaire la vue synthese

à long terme
============

* Génération de tables et de modèles à partir de la conf pour avoir des données en dur (et plus en jsonb)
* Composants choix du site & persistance de certains champs pour une saisie rapide (cheveches)
* Saisie rapide avec formulaire sous forme de ligne dans le tableau
* Alternatives à ngx-datatable?

====
Fait
====

petites modifications
=====================

à long terme
============
