# Module monitoring 

## Sommaire

* [Concepts du module](#concepts)
* [Installation du module](#installation)
* [Installation d'un sous module](#installation-dun-sous-module)
* [Configuration des champs spécifiques d'un sous-module](docs/sous_module.md)
* [Gestion des sites et groupes de site](docs/gestion_sites_groupes_de_site.md)
* [Permissions](#permissions)
* [Base de données](#base-de-données)
* [Gestion de la synthèse](docs/synthese.md)
* [Documentation technique](docs/documentation_technique.md)
* [Liste des commandes](docs/commandes.md)

## Concepts

Ce module permet de générer de façon générique des interfaces de saisies correspondant à des protocoles de suivi.
Par "suivi", on entend un protocole dont le point d'entrée est un site géographique, sur lequel on va revenir régulièrement effectuer des relevés. Il s'oppose par sa structure au module "Occtax" dont l'objecif est de faire de la saisie de données opportunistes (sans revenir régulièrement sur le même site de suivi).

Le module est articulé autour des trois concepts :

- les sites : l'objet géographique de suivi (qui peuvent être regroupés en groupe de sites)
- les visites : une visite est effectué sur un site (date, observateurs)
- le observations : observations faites durant la visite (espèces)

Les 3 niveaux que sont le site, les visites et les observations sont fourni avec un tronc commun (les champs génériques) qui peuvent être complétés par des champs spécifiques à chaque protocole. Ces champs spécifiques sont défini par des fichiers de configurations JSON.
Pour chaque sous-module, correspondant à un protocole spécifique de suivi, il est ainsi possible d'ajouter dynamiquement des champs de différents types (liste, nomenclature, booléen, date, radio, observateurs, texte, taxonomie...). Ceux-ci peuvent être obligatoires ou non, affichés ou non et avoir des valeurs par défaut (voir doc détaillé : [Création d'un sous-module](docs/sous_module.md)
)

![Liste des sites du protocole de test](docs/images/apercu.png)



## Installation

### Pré-requis

* Avoir GeoNature installé dans une version compatible avec celle de la version du module.

### Récupération du dépôt

Pour récupérer le code source du module, vous pouvez le télécharger ou le cloner.

#### Téléchargement

```sh
wget https://github.com/PnX-SI/gn_module_monitoring/archive/X.Y.Z.zip
unzip X.Y.Z.zip
rm X.Y.Z.zip
mv gn_module_monitoring-X.Y.Z gn_module_monitoring
```
Avec `X`, `Y`, `Z` correspondant à la version souhaitée.

#### Clonage du dépôt

```sh
git clone https://github.com/PnX-SI/gn_module_monitoring.git
```

### Installation du module

```sh
source ~/geonature/backend/venv/bin/activate
geonature install-gn-module ~/gn_module_monitoring MONITORINGS
sudo systemctl restart geonature
deactivate
```

Créer le dossier suivant dans le dossier `media` de GeoNature

```sh
mkdir ~/geonature/backend/media/monitorings
```

Il vous faut désormais attribuer des permissions aux groupes ou utilisateurs que vous souhaitez, pour qu'ils puissent accéder et utiliser le module (voir <https://docs.geonature.fr/admin-manual.html#gestion-des-droits>). Si besoin une commande permet d'attribuer automatiquement toutes les permissions dans tous les modules à un groupe ou utilisateur administrateur.

### Mise à jour

Pour mettre à jour le modue monitoring, suivre la documentation de [mise à jour d'un module GeoNature](https://docs.geonature.fr/installation.html#mise-a-jour-du-module)

### Configuration générale du module monitoring

Un fichier de config `monitorings_config.toml.example` peut être modifié puis copié à la racine du dossier de config de GeoNature : `~/geonature/config`.

Trois champs sont paramétrable :

- `TITLE_MODULE` : Titre présent sur la page d'accueil du module monitoring
- `DESCRIPTION_MODULE` : Description du module monitoring également présente sur la page d'accueil
- `CODE_OBSERVERS_LIST` : Code de la liste d'observateur qui est utilisé par défaut

### Installation d'un sous-module

#### Récupérer le répertoire de configuration d'un sous-module de suivi

Par exemple le sous-module `test` présent dans le repertoire `contrib/test` du module de suivi.

#### Activer le venv de GeoNature

```sh
source ~/geonature/backend/venv/bin/activate
```

#### Copie du dossier de configuration

Créer un dossier pour référencer les configurations des sous-modules dans GeoNature (`geonature/backend/media/monitorings`) :

```sh
mkdir geonature/backend/media/monitorings
```

Créer un lien symbolique vers le dossier du sous-module dans le dossier `media` de GeoNature :

```sh
ln -s <chemin absolu du dossier du sous-module> ~/geonature/backend/media/monitorings/<nom du dossier du sous-module>
```

Exemple pour le module "test" : 

```
ln -s ~/gn_module_monitoring/contrib/test ~/geonature/backend/media/monitorings/test
```

#### Lancer la commande d'installation du sous-module

```sh
geonature monitorings install <module_code>
```

Si le code du sous-module n'est pas renseigné ou si le dossier du sous-module n'existe pas, la commande va afficher la liste des sous-modules installés et disponibles.

```sh
geonature monitorings install
```

La commande va fournir la sortie suivante :

```
Modules disponibles :

- module3: Module 3 (Troisième exemple de module)
- module4: Module 4 (...)
- module5: Module 5 (...)
- <module_code>: <module_label> (<module_desc>)

Modules installés :

- module1: Module 1 (Premier exemple de module)
- module2: Module 2 (Deuxième exemple de module)
```

Il vous faut désormais attribuer des permissions aux groupes ou utilisateurs que vous souhaitez, pour qu'ils puissent accéder et utiliser le sous-module (voir <https://docs.geonature.fr/admin-manual.html#gestion-des-droits>). Si besoin une commande permet d'attribuer automatiquement toutes les permissions dans tous les modules à un groupe ou utilisateur administrateur.

### Configurer le sous-module

#### Dans le menu de droite de GeoNature, cliquer sur le module "Monitorings"

Le sous-module installé précedemment doit s'afficher dans la liste des sous-modules.

#### Cliquez sur le sous-module

Vous êtes désormais sur la page du sous-module. Un message apparaît pour vous indiquer de configurer celui-ci.

#### Cliquez sur le bouton `Éditer`

Le formulaire d'édition du sous-module s'affiche et vous pouvez choisir les variables suivantes :

* Jeux de données *(obligatoire)* :
    * Un module peut concerner plusieurs jeux de données, le choix sera ensuite proposé au niveau de chaque visite.
* Liste des observateurs *(obligatoire)* :
    * La liste d'observateurs définit l'ensemble des observateurs possibles pour le module (et de descripteurs de site).
    * Cette liste peut être définie dans l'application `UsersHub`.
* Liste des taxons *(obligatoire selon le module)* :
    * Cette liste définit l'ensemble des taxons concernés par ce module. Elle est gérée dans l'application `TaxHub`.
* Activer la synthèse *(non obligatoire, désactivée par défaut)* ?
    * Si on décide d'intégrer les données du sous-module dans la synthèse de GeoNature.
* Affichage des taxons *(obligatoire)* ?
    * Définit comment sont affichés les taxons dans le module :
        * `lb_nom` : Nom latin,
        * `nom_vern,lb_nom` : Nom vernaculaire par defaut s'il existe, sinon nom latin.
* Afficher dans le menu ? *(non obligatoire, non affiché par défaut)* :
    * On peut décider que le sous-module soit accessible directement depuis le menu de gauche de GeoNature.
    * `active_frontend`
* Type de site :
    * Permet d'associer des sites créé dans le gestionnaire de site à un module. Tous les sites dont le type est défini ici remonteront dans le module ( [voir documentation sur le gestionnaire de sites  (#gestionnaire-de-sites) )
* Options spécifiques du sous-module :
    * Un sous-module peut présenter des options qui lui sont propres et définies dans les paramètres spécifiques du sous-module.
    

### Configuration des champs spécifiques du sous-module

Maintenant que le sous-module est installé, vous pouvez ajouter des champs spécifiques pour le faire correspondre à votre protocole de suivi.
Le documentation détaillé de la configuration des champs additionnels est ici :  [Configuration des champs d'un sous module](docs/sous_module.md)

Des exemples de sous-modules sont disponibles sur le dépôt
<https://github.com/PnX-SI/protocoles_suivi/> :

* Protocole de suivi des oedicnèmes,
* Protocole de suivi des mâles chanteurs de l'espèce chevêche
    d'Athena;
* Protocole Suivi Temporel des Oiseaux de Montagne (STOM)
* Autres...

## Gestionnaire de sites

Chaque module permet de créer ses propres sites et groupe de sites. Cependant certains sites peuvent faire l'objet de plusieurs protocoles de suivi, c'est pouquoi le module monitoring offre la possibilité de créer des sites et des groupes de site dans le **gestionnaire de site** et de les mobiliser dans plusieurs sous-modules.

![Page d'accueil accès aux sites](docs/images/page_accueil_monitoring_acces_sites.png)

Dans le gestionnaire de site il est possible de créer, éditer, supprimer, modifier des sites et des groupes de site de manière indépendante à la gestion de sous modules. Il est également possible de saisir directement des visites et des observations en rattachant les visites au sous-module que l'on souhaite.

> [!IMPORTANT]
> **Associer un site à un module**
>
> Plutôt que d'associer un à un les sites à des modules, l'association entre un site et un module se fait via la notion de **type de site**. Une type de site est un concept permettant de regrouper des sites qui font l'objet de multiples protocoles et qui partage potentiellement une série de descripteurs communs. 
>
> Un "point d'écoute" qui va par exemple faire l'objet de plusieurs protocoles ornithologiques (STOC, oiseaux migrateurs etc...) peut être définit comme un type de site.
>
> Lors de la configuration d'un module (en interface), on doit associer le module à un ou des types de site. Tous les sites créés via le gestionnaire de site dont le type correspond à celui définit au niveau du module, remonteront dans la liste des sites du module.
>
> **Associer un groupe de sites à un module**
>
> L'association entre un groupe de site et un module se fait elle directement. Lorsque l'on crée un groupe de site dans le gestionnaire de site, on l'associe directement à un ou plusieurs groupes de site


**Définir des champs spécifique à un type de site**

Il est possible de définir des champs spécifiques communs à des type de sites.
Contrairement aux configurations des modules, celle-ci ne se fait pas dans un fichier JSON, mais dans le backoffice de GeoNature (rubrique monitoring / type de sites).

![admin type de sites](docs/images/admin_type_site.png)

La syntaxe est la même que pour la création de champs d'un sous-module (voir [Création d'un sous-module](docs/sous_module.md)
). La clé `specific` permettant de configurer les champs et la clé `display_properties` d'afficher les champs sur les fiches info des sites.

## Permissions

Les permissions peuvent désormais être définies avec une notion de portée ('mes données', 'les données de mon organisme', 'toutes les données' si on ne précise pas de portée mais qu'on accorde une permission). Ces permissions peuvent être définies sur chaque objet défini ci dessous.

La gestion des permissions pour les rôles (utilisateur ou groupe) se réalise au niveau de l'interface d'administration des permissions de GeoNature.

Les permissions sont définis par sous-modules pour chaque type d'objet (modules, groupes de sites, sites, visites, observations et types de site) :

- `MONITORINGS_MODULES` - R : permet a l'utilisateur d'accéder au module, de le voir dans la liste des modules
- `MONITORINGS_MODULES` - U : action administrateur qui permet de configurer le module et de synchroniser la synthèse
- `MONITORINGS_MODULES` - E : action qui permet aux utilisateurs d'exporter les données (si défini par le module)
- `MONITORINGS_GRP_SITES` - CRUD : action de lire, créer, modifier, supprimer un groupe de site
- `MONITORINGS_SITES` - CRUD : action de lire, créer, modifier, supprimer un site
- `MONITORINGS_VISITES` - CRUD : action de lire, créer, modifier, supprimer les visites, observations, observations détails
- `TYPES_SITES`- CRUD : action de lire, créer, modifier, supprimer les types de sites via l'interface administrateur (uniquement pour le module monitorings et non les sous modules)

Par défaut, dès qu'un utilisateur a un droit supérieur à 0 pour une action (c-a-d aucune portée) il peut réaliser cette action.

Il est possible de mettre à jour les permissions disponibles pour un module en utilisant la commande `update_module_available_permissions`


## Base de données

Le module permet de générer des sous-modules (stockés dans la table `gn_commons.t_modules`) pour chaque protocole de suivi. Ils s'appuient sur les champs fixes des 3 tables `gn_monitoring.t_base_sites`, `gn_monitoring.t_base_visits` et `gn_monitoring.t_observations` qui peuvent chacunes être étendues avec des champs spécifiques et dynamiques stockés dans des champs de type `JSONB`.


Des fonctions SQL ainsi qu'une vue définie pour chaque protocole permettent d'alimenter automatiquement la synthèse de GeoNature à partir des données saisies dans chaque sous-module.



Les sites et groupes de sites multi modules.

![MCD du schema gn_monitoring](docs/images/2023-10-MCD_schema_monitoring.png)

