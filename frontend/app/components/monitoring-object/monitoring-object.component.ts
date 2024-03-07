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
import { ConfigJsonService } from '../../services/config-json.service';
import { GeoJSONService } from '../../services/geojson.service';

@Component({
  selector: 'pnx-object',
  templateUrl: './monitoring-object.component.html',
  styleUrls: ['./monitoring-object.component.css'],
})
export class MonitoringObjectComponent implements OnInit {
  obj: MonitoringObject;
  module: MonitoringObject;

  filters: Object = {};
  pre_filters: Object = {};
  selectedObject: Object = undefined;
  objectListType: String;

  backendUrl: string;
  frontendModuleMonitoringUrl: string;

  objForm: FormGroup;

  checkEditParam: boolean;
  bEdit = false;
  bLoadingModal = false;

  currentUser: User;

  objectsStatus: Object = {};
  heightMap;

  moduleSet = false;
  bDeleteModal = false;

  constructor(
    private _route: ActivatedRoute,
    private _objService: MonitoringObjectService,
    private _configService: ConfigService,
    private _dataUtilsService: DataUtilsService,
    private _formBuilder: FormBuilder,
    public mapservice: MapService,
    private _auth: AuthService,
    private _commonService: CommonService,
    private _evtObjService: ObjectService,
    private _geojsonService: GeoJSONService
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
          return this.getDataObject(); // récupération des données de l'object selon le type (module, site, etc..)
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
        this.initFilters();
        this.evenListnerTable();
      });
  }

  onEachFeatureSite() {
    return (feature, layer) => {};
  }

  initCurrentUser() {
    this.currentUser = this._auth.getCurrentUser();
    this.currentUser['moduleCruved'] = this._configService.moduleCruved(this.obj.moduleCode);
  }

  getModuleSet() {
    // Verifie si le module est configué
    this.module.get(0).subscribe(() => {
      const schema = this._configService.schema(this.module.moduleCode, 'module');
      const moduleFieldList = Object.keys(
        this._configService.schema(this.module.moduleCode, 'module')
      ).filter((key) => schema[key].required);
      this.moduleSet = moduleFieldList.every(
        (v) => ![null, undefined].includes(this.module.properties[v] || this.obj.properties[v])
      );
    });
  }

  initFilters() {
    this.pre_filters = {};
    return this.module.get(1).subscribe(() => {
      // modules
      this.pre_filters['modules'] = this.module.id;

      // filtre objet géographique de référence
      if (this.obj.objectType == 'sites_group') {
        this.pre_filters['id_sites_group'] = this.obj.id;
      } else if (this.obj.objectType == 'site') {
        this.pre_filters['id_base_site'] = this.obj.id;
      } else if (this.obj['siteId'] !== undefined) {
        // affichage du site parent
        this.pre_filters['id_base_site'] = this.obj['siteId'];
      }
    });
  }

  // initSites() {
  //   return this.module.get(1).subscribe(() => {
  //     // TODO liste indépendantes carte et listes

  //     // affichage des groupes de site uniquement si l'objet est un module
  //     if (this.obj.objectType == 'module' && this.obj['children']['sites_group']) {
  //       const sitesGroup = this.obj['children']['sites_group'];
  //       this.sitesGroup = {
  //         features: sitesGroup.map((group) => {
  //           group['id'] = group['properties']['id_sites_group'];
  //           group['type'] = 'Feature';
  //           return group;
  //         }),
  //         type: 'FeatureCollection',
  //       };
  //     }
  //     // affichage des sites du premier parent qui a des sites dans l'odre de parent Path
  //     let sites = null;
  //     let cur = this.obj;
  //     do {
  //       sites = cur['children']['site'];
  //       cur = cur.parent();
  //     } while (!!cur && !sites);

  //     if (!sites) {
  //       return;
  //     }
  //     this.sites = {
  //       features: sites.map((site) => {
  //         site['id'] = site['properties']['id_base_site'];
  //         site['type'] = 'Feature';
  //         return site;
  //       }),
  //       type: 'FeatureCollection',
  //     };
  //     this.initObjectsStatus();
  //   });
  // }

  // initObjectsStatus() {
  //   const objectsStatus = {};
  //   for (const childrenType of Object.keys(this.obj.children)) {
  //     objectsStatus[childrenType] = this.obj.children[childrenType].map((child) => {
  //       return {
  //         id: child.id,
  //         selected: false,
  //         visible: true,
  //         current: false,
  //       };
  //     });
  //   }

  //   // init site status
  //   if (this.obj.siteId) {
  //     objectsStatus['site'] = [];
  //     this.sites['features'].forEach((f) => {
  //       // determination du site courrant
  //       let cur = false;
  //       if (f.properties.id_base_site == this.obj.siteId) {
  //         cur = true;
  //       }

  //       objectsStatus['site'].push({
  //         id: f.properties.id_base_site,
  //         selected: false,
  //         visible: true,
  //         current: cur,
  //       });
  //     });
  //   }

  //   this.objectsStatus = objectsStatus;
  // }

  initRoutesParams() {
    return this._route.paramMap.pipe(
      mergeMap((params) => {
        const objectType = params.get('objectType') ? params.get('objectType') : 'module';

        this.obj = new MonitoringObject(
          params.get('moduleCode'),
          objectType,
          params.get('id'),
          this._objService
        );

        this.obj.parentsPath = this._route.snapshot.queryParamMap.getAll('parents_path') || [];
        this.module = new MonitoringObject(
          params.get('moduleCode'),
          'module',
          null,
          this._objService
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
          return this._objService
            .configService()
            .loadConfigSpecificConfig(this.obj)
            .pipe(
              tap((config) => {
                this.obj.template_specific = this._objService
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
    this.getModuleSet();
    return this._dataUtilsService.getInitData(this.obj.moduleCode);
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
    return this.obj.getParents(1);
  }

  onObjChanged(obj: MonitoringObject) {
    this.obj = obj;
    if (obj['objectType'] === 'site' || obj['objectType'] === 'sites_group') {
      // this.initSites();
      this.initFilters();
    }
    this.getModuleSet();
  }

  onDeleteFromTable(event) {
    return this._objService
      .dataMonitoringObjectService()
      .deleteObject(this.obj.moduleCode, event.objectType, event.rowSelected.id);
  }

  evenListnerTable() {
    const $displayModal = this._evtObjService.currentDeleteModal;
    const $rowSelected = this._evtObjService.currentRowSelected;
    $displayModal
      .pipe(
        distinctUntilChanged((prev, curr) => prev === curr),
        tap((displayModal) => {
          this.bDeleteModal = displayModal;
        }),
        concatMap(() => {
          return $rowSelected;
        }),
        concatMap((rowSelected) => {
          return this.onDeleteFromTable(rowSelected).pipe(
            distinctUntilChanged((prev, curr) => prev.rowSelected === curr.rowSelected)
          );
        }),
        catchError((err) => {
          console.log(err);
          this._evtObjService.changeDisplayingDeleteModal(false);
          return of(null);
        })
      )
      .subscribe((deletedObj) => {
        // this.initSites();
        this.initFilters();
        this._evtObjService.changeDisplayingDeleteModal(false);
      });
  }
}
