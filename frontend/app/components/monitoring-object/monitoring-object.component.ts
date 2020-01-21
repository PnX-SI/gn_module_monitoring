import { Observable, of, forkJoin } from '@librairies/rxjs';
import { mergeMap, concatMap } from '@librairies/rxjs/operators';

import { MonitoringObject } from '../../class/monitoring-object';
import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder } from '@angular/forms';


// services
import { ActivatedRoute } from '@angular/router';
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ConfigService } from '../../services/config.service';
import { DataUtilsService } from '../../services/data-utils.service';
import { MapService } from '@geonature_common/map/map.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { Utils } from '../../utils/utils';
@Component({
  selector: 'pnx-object',
  templateUrl: './monitoring-object.component.html',
  styleUrls: ['./monitoring-object.component.css']
})
export class MonitoringObjectComponent implements OnInit {

  obj: MonitoringObject;
  module: MonitoringObject;
  sites: {};

  backendUrl: string;
  frontendModuleMonitoringUrl: string;

  objForm: FormGroup;

  bEdit = false;
  bLoadingModal = false;

  currentUser: User;

  objectsStatus: Object = {};

  constructor(
    private _route: ActivatedRoute,
    private _objService: MonitoringObjectService,
    private _configService: ConfigService,
    private _dataUtilsService: DataUtilsService,
    private _formBuilder: FormBuilder,
    public mapservice: MapService,
    private _auth: AuthService,
  ) { }

  ngOnInit() {

    this.currentUser = this._auth.getCurrentUser();

    of(true)
      .pipe(
        mergeMap(() => {
          return this.initParams();
        }),
        mergeMap(() => {
          return this.initConfig(); // initialisation de la config
        }),

        mergeMap(() => {
          return this.initData(); // recupérations des données Nomenclature, Taxonomie, Utilisateur.. et mise en cache
        }),

        mergeMap(() => {
          return this.getDataObject(); // récupération des données de l'object selon le type (module, site, etc..)
        })
      )
      .subscribe(() => {
        this.obj.initTemplate(); // pour le html
        this.initSites();
        this.bLoadingModal = false; // fermeture du modal
        this.obj.bIsInitialized = true; // obj initialisé
        // si on est sur une création (pas d'id et id_parent ou pas de module_path pour module (root))
        this.bEdit = this.bEdit || (this.obj.isRoot() && !this.obj.modulePath) || (!this.obj.id && !!this.obj.parentId);

        this.initObjectsStatus();

      });
  }

  initSites() {
    const sites = this.module['children']['site'];
    this.sites = {
      features: sites.map((site) => {
        site['id'] = site['properties']['id_base_site'];
        site['type'] = 'Feature';
        return site;
      }),
      type: 'FeatureCollection'
    };
  }

  initObjectsStatus() {
    const $this = this;
    const objectsStatus = {};
    for (const childrenType of Object.keys(this.obj.children)) {
      objectsStatus[childrenType] = this.obj
        .children[childrenType]
        .map((child) => {
          return {
            'id': child.id,
            'selected': false,
            'visible': true
          };
        });
    }

    // init site status
    if (this.obj.siteId) {
      if (!objectsStatus['site']) {
        objectsStatus['site'] = [
          {
            'id': this.obj.siteId,
            'selected': true,
            'visible': true,
            'current': true
          }
        ];
      } else {
        const siteStatus = objectsStatus['site'] && objectsStatus['site'].find((status) => status.id === this.obj.siteId);
        siteStatus['selected'] = true;
        siteStatus['current'] = true;
      }
    }
    this.objectsStatus = objectsStatus;
  }

  initParams() {
    return this._route.paramMap
      .pipe(
        mergeMap((params) => {

          const objectType = params.get('objectType') ? params.get('objectType') : 'module';

          this.obj = new MonitoringObject(params.get('modulePath'),
          objectType,
          params.get('id'),
          this._objService
          );

          this.module = new MonitoringObject(params.get('modulePath'),
          'module',
          null,
          this._objService
          );

          this.obj.parentId = params.get('parentId');
          return this._route.queryParamMap;
        }),
        mergeMap((params) => {
          this.objForm = this._formBuilder.group({});
          this.bEdit = !!params.get('edit');
          return of(true);
        })
      );
  }

  initConfig(): Observable<any> {
    return this._configService.init(this.obj.modulePath)
      .pipe(
        mergeMap(() => {
          this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
          this.backendUrl = this._configService.backendUrl();
          return of(true);
        })
      );
  }

  initData(): Observable<any> {
    return this._dataUtilsService.getInitData(this.obj.modulePath);
  }

  getDataObject(): Observable<any> {
    // TODO mettre au propre
    const observables = {
      'module': this.module.get(1)
    };
    if (this.obj.objectType !== 'module') {
      observables['obj'] = this.obj.get(1);
    }

    return forkJoin(observables)
      .pipe(
        concatMap((res) => {
          if (this.obj.objectType === 'module') {
            return this.obj.get(1);
          }
          return of(true);
        })
      );
  }
}
