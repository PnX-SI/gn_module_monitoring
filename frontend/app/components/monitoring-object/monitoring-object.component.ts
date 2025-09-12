import { Observable, of, forkJoin } from 'rxjs';
import {
  mergeMap,
  concatMap,
  map,
  tap,
  take,
  takeUntil,
  distinctUntilChanged,
  catchError,
  skipWhile,
} from 'rxjs/operators';

import { MonitoringObject } from '../../class/monitoring-object';
import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder } from '@angular/forms';

// services
import { ActivatedRoute } from '@angular/router';
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ConfigService } from '../../services/config.service';
import { DataUtilsService } from '../../services/data-utils.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { CommonService } from '@geonature_common/service/common.service';
import { MapService } from '@geonature_common/map/map.service';
import { ObjectService } from '../../services/object.service';

import { Utils } from '../../utils/utils';
import { GeoJSONService } from '../../services/geojson.service';
import { ListService } from '../../services/list.service';
@Component({
  selector: 'pnx-object',
  templateUrl: './monitoring-object.component.html',
  styleUrls: ['./monitoring-object.component.css'],
})
export class MonitoringObjectComponent implements OnInit {
  obj: MonitoringObject;
  module: MonitoringObject;

  selectedObject: Object = undefined;
  forceReload: boolean = false;

  backendUrl: string;
  frontendModuleMonitoringUrl: string;

  objForm: FormGroup;

  checkEditParam: boolean;
  bEdit = false;
  bLoadingModal = false;

  currentUser: User;

  heightMap;

  moduleSet = false;
  bDeleteModal = false;

  constructor(
    private _route: ActivatedRoute,
    private _monitoringObjService: MonitoringObjectService,
    private _objectService: ObjectService,
    private _configService: ConfigService,
    private _dataUtilsService: DataUtilsService,
    private _formBuilder: FormBuilder,
    public mapservice: MapService,
    private _auth: AuthService,
    private _commonService: CommonService,
    private _evtObjService: ObjectService,
    private _geojsonService: GeoJSONService,
    public _listService: ListService
  ) {}

  ngAfterViewInit() {
    const container = document.getElementById('object');
    const height = this._commonService.calcCardContentHeight();
    container.style.height = height - 40 + 'px';
    setTimeout(() => {
      this.heightMap = height - 80 + 'px';
    });
  }

  ngOnInit() {
    const elements = document.getElementsByClassName('monitoring-map-container');
    if (elements.length >= 1) {
      elements[0].remove();
    }
    of(true)
      .pipe(
        mergeMap(() => {
          return this.initRoutesParams(); // parametres de route
        }),
        mergeMap(() => {
          return this.initConfig(); // initialisation de la config
        }),
        mergeMap(() => {
          this.initCurrentUser();
          return this.initData(); // recupérations des données Nomenclature, Taxonomie, Utilisateur.. et mise en cache
        }),
        mergeMap(() => {
          return this.getParents(); // récupération des données de l'object selon le type (module, site, etc..)
        }),
        tap(() => {
          // if (this.obj.objectType == 'sites_group') {
          //   this._geojsonService.removeAllFeatureGroup();
          //   this.obj.geometry
          //     ? this._geojsonService.setGeomSiteGroupFromExistingObject(this.obj.geometry)
          //     : null;
          // }
        })
      )
      .subscribe(() => {
        this.obj.initTemplate(); // pour le html
        this.bEdit = this.checkEditParam == true ? true : false;
        // si on est sur une création (pas d'id et id_parent ou pas de module_code pour module (root))
        this.bEdit =
          this.bEdit ||
          (this.obj.isRoot() && !this.obj.moduleCode) ||
          (!this.obj.id && !!this.obj.parentId);
        this.bLoadingModal = false; // fermeture du modal
        this.obj.bIsInitialized = true; // obj initialisé
        // breadcrumb
        const queryParams = this._route.snapshot.queryParams || {};
        this._objectService.loadBreadCrumb(
          this.obj.moduleCode,
          this.obj.objectType,
          this.obj.id,
          queryParams
        );
      });
  }

  onEachFeatureSite() {
    return (feature, layer) => {};
  }

  initCurrentUser() {
    this.currentUser = this._auth.getCurrentUser();
    this.currentUser['moduleCruved'] = this._configService.moduleCruved(this.obj.moduleCode);
  }

  getModuleSet(): Observable<any> {
    // TODO ANALYSER A QUOI SERT CETTE FONCTION
    // Surrement à supprimer quand la configuration du module sera chargée en behaviourSubject
    // récupération des données de l'object selon le type (module, site, etc..)
    return this.module.get(0).pipe(
      mergeMap(() =>
        this.getDataObject().pipe(
          tap(() => {
            const schema = this._configService.schema(this.module.moduleCode, 'module');
            const moduleFieldList = Object.keys(
              this._configService.schema(this.module.moduleCode, 'module')
            ).filter((key) => schema[key].required);
            this.moduleSet = moduleFieldList.every(
              (v) =>
                ![null, undefined].includes(this.module.properties[v] || this.obj.properties[v])
            );

            this.initPreFilters();
          })
        )
      )
    );
  }

  initPreFilters() {
    // modules
    const queryParams = this._route.snapshot.queryParams || {};
    let pre_filters = this._listService.preFilters;
    pre_filters['site']['module_context'] = this.obj.moduleCode;
    pre_filters['sites_group']['module_context'] = this.obj.moduleCode;

    pre_filters['site']['types_site'] = Object.keys(
      this._configService.config()[this.obj.moduleCode]['module']['types_site']
    );
    if (this.obj.objectType == 'module') {
      pre_filters['sites_group']['modules'] = this.obj.properties['id_module'];
    }
    if (this.obj.objectType == 'sites_group') {
      pre_filters['sites_group']['id_sites_group'] = this.obj.id;
      pre_filters['site']['id_sites_group'] = this.obj.id;
    } else if (this.obj.objectType == 'site') {
      pre_filters['site']['id_base_site'] = this.obj.id;
    } else if (this.obj['siteId'] !== undefined) {
      // affichage du site parent
      pre_filters['site']['id_base_site'] = this.obj['siteId'];
    } else if (queryParams['id_base_site'] !== undefined) {
      // récupération du site parent via l'url
      pre_filters['site']['id_base_site'] = queryParams['id_base_site'];
    } else if (queryParams['siteId'] !== undefined) {
      // récupération du site parent via l'url
      pre_filters['site']['id_base_site'] = queryParams['siteId'];
    }

    this._listService.preFilters = pre_filters;

    // L'objet n'a aucun enfant initialisation du paramètre listType
    if (Object.keys(this.obj.children || []).length == 0) {
      this._listService.tableFilters = {};
      if (this.obj.objectType == 'sites_group') {
        this._listService.listType = 'sites_group';
      } else {
        this._listService.listType = 'site';
      }
    } else {
      this._listService.listType = this.obj.children0Array()[0].objectType;
    }
  }

  initRoutesParams() {
    return this._route.paramMap.pipe(
      mergeMap((params) => {
        const objectType = params.get('objectType') ? params.get('objectType') : 'module';
        this.obj = new MonitoringObject(
          params.get('moduleCode'),
          objectType,
          params.get('id'),
          this._monitoringObjService
        );

        this.obj.parentsPath = this._route.snapshot.queryParamMap.getAll('parents_path') || [];
        this.module = new MonitoringObject(
          params.get('moduleCode'),
          'module',
          null,
          this._monitoringObjService
        );
        this.objForm = this._formBuilder.group({});

        if (params.get('edit')) {
          this.checkEditParam = Boolean(params.get('edit'));
        } else {
          this.checkEditParam = false;
        }
        // query param snapshot

        // this.obj.parentId = params.get('parentId') && parseInt(params.get('parentId'));
        return of(true);
      })
    );
  }

  initConfig(): Observable<any> {
    return this._configService.init(this.obj.moduleCode).pipe(
      concatMap(() => {
        if (this.obj.objectType == 'site' && this.obj.id != null) {
          return this._monitoringObjService
            .configService()
            .loadConfigSpecificConfig(this.obj)
            .pipe(
              tap((config) => {
                this.obj.template_specific = this._monitoringObjService
                  .configService()
                  .addSpecificConfig(config);
              })
            );
        } else {
          return of(null);
        }
      }),
      mergeMap(() => {
        this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
        this.backendUrl = this._configService.backendUrl();
        return of(true);
      })
    );
  }

  initData(): Observable<any> {
    // Réinitialisation des services
    this._listService.reinitializeObservables();

    return of(true).pipe(
      mergeMap(() => {
        // A voir ce que fait cette fonction
        return this.getModuleSet();
      }),
      mergeMap(() => {
        // Récupération des données nomenclatures utilisées dans le module
        // Ce qui permet de les stocker en cache pour les réutiliser dans les formulaires
        //  notamment pour la variable meta
        return this._dataUtilsService.initModuleNomenclatures(this.module.moduleCode);
      })
    );
  }

  getDataObject(): Observable<any> {
    if (!this.obj.deleted) {
      return this.obj.get(1);
    }

    return of(this.obj);
  }

  getParents(): Observable<any> {
    const queryParams = this._route.snapshot.queryParams;
    for (const key of Object.keys(queryParams)) {
      const strToInt = parseInt(queryParams[key]);
      if (!Number.isNaN(strToInt)) {
        this.obj.properties[key] = strToInt;
      }
    }
    return this.obj.getParents(0, this._configService.moduleCruved(this.obj.moduleCode));
  }

  onDeleteRowChange(event) {
    this.getDataObject().subscribe((obj) => {
      this.forceReload = true;
    });
  }
}
