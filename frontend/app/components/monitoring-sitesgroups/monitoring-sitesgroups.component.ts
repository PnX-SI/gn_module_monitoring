import { Location } from '@angular/common';
import { Component, EventEmitter, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { breadCrumbBase } from '../../class/breadCrumb';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { MonitoringObject } from '../../class/monitoring-object';
import { IDataTableObj, ISite, ISitesGroup } from '../../interfaces/geom';
import { Module } from '../../interfaces/module';
import { IBreadCrumb, SelectObject } from '../../interfaces/object';
import { IobjObs } from '../../interfaces/objObs';
import { IPage, IPaginated } from '../../interfaces/page';
import { IIndividual } from '../../interfaces/individual';
import {
  IndividualsService,
  SitesGroupService,
  SitesService,
} from '../../services/api-geom.service';
import { ConfigJsonService } from '../../services/config-json.service';
import { ConfigService } from '../../services/config.service';
import { FormService } from '../../services/form.service';
import { GeoJSONService } from '../../services/geojson.service';
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ObjectService } from '../../services/object.service';
import { TPermission } from '../../types/permission';
import { Popup } from '../../utils/popup';

import { CacheService } from '../../services/cache.service';

const LIMIT = 10;

import { Observable, ReplaySubject, forkJoin, of } from 'rxjs';
import { map, mergeMap, takeUntil } from 'rxjs/operators';

@Component({
  selector: 'monitoring-sitesgroups',
  templateUrl: './monitoring-sitesgroups.component.html',
  styleUrls: ['./monitoring-sitesgroups.component.css'],
})
export class MonitoringSitesGroupsComponent extends MonitoringGeomComponent implements OnInit {
  page: IPage;

  obj;

  colsname: {};
  objectType: IobjObs<ISitesGroup>;
  objForm: FormGroup;
  objInitForm: Object = {};
  breadCrumbElementBase: IBreadCrumb = breadCrumbBase.baseBreadCrumbSiteGroups.value;

  rows;
  dataTableObj: IDataTableObj;
  dataTableArray: {}[] = [];
  activetabIndex: number;
  currentRoute: string;
  // siteGroupEmpty={
  //   "comments" :'',
  //   sites_group_code: string;
  //   sites_group_description: string;
  //   sites_group_name: string;
  //   uuid_sites_group: string; //FIXME: see if OK
  // }
  modules: SelectObject[];
  modulSelected;
  siteSelectedId: number;
  private destroyed$: ReplaySubject<boolean> = new ReplaySubject(1);

  siteResolvedProperties;

  bDeleteModalEmitter = new EventEmitter<boolean>();

  currentUser: User;
  currentPermission: TPermission;

  moduleCode: string;

  bEdit: false;

  config;

  constructor(
    private _auth: AuthService,
    private _sites_group_service: SitesGroupService,
    private _sitesService: SitesService,
    private _individualService: IndividualsService,
    public geojsonService: GeoJSONService,
    private router: Router,
    private _objService: ObjectService,
    private _formBuilder: FormBuilder,
    private _configJsonService: ConfigJsonService,
    private _Activatedroute: ActivatedRoute, // private _routingService: RoutingService
    private _formService: FormService,
    private _location: Location,
    private _popup: Popup,
    private _monitoringObjectService: MonitoringObjectService,
    private _configService: ConfigService,
    private _cacheService: CacheService
  ) {
    super();
    this.getAllItemsCallback = this.getData; //[this.getSitesGroups, this.getSites];
  }

  ngOnInit() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
    this.initSiteGroup();
    this._objService.changeSelectedObj({}, true);
    // this._formService.changeFormMapObj({frmGp: this._formBuilder.group({}),bEdit:false, objForm: {}})
  }

  initSiteGroup() {
    this._Activatedroute.data.subscribe(({ data }) => {
      let objectObs;
      let currentData;
      let currentObjConfig;
      if (data.route == 'site') {
        objectObs = this._sitesService.objectObs;
        currentData = data.sites.data;
        currentObjConfig = data.sites.objConfig;
      } else if (data.route == 'individual') {
        objectObs = this._individualService;
        currentData = data.individuals.data;
        currentObjConfig = data.individuals.objConfig;
      } else {
        objectObs = this._sites_group_service.objectObs;
        currentData = data.sitesGroups.data;
        currentObjConfig = data.sitesGroups.objConfig;
      }

      this._objService.changeObjectTypeParent(objectObs);
      this._objService.changeObjectType(objectObs);

      this.currentRoute = data.route;
      this.moduleCode = data.moduleCode;
      this.geojsonService.setModuleCode(`${this.moduleCode}`);
      this.currentUser = this._auth.getCurrentUser();
      this.currentUser['moduleCruved'] = this._configService.moduleCruved(this.moduleCode);

      this.currentPermission = data.permission;

      this.page = {
        count: currentData.count,
        limit: currentData.limit,
        page: currentData.page - 1,
      };
      // this.columns = [data.sitesGroups.data.items, data.sites.data.items]
      this.colsname = currentObjConfig.dataTable.colNameObj;

      const { route, permission, moduleCode, ...dataToTable } = data;

      this.setDataTableObj(dataToTable);

      // Indentify active tab
      this.activetabIndex = this.getdataTableIndex(data.route);

      if (data.route == 'site') {
        this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSites.value;
        this.currentPermission.MONITORINGS_SITES.canRead ? this.getGeometriesSite() : null;
      } else {
        this.currentPermission.MONITORINGS_GRP_SITES.canRead
          ? this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups())
          : null;
      }

      if (this.moduleCode !== 'generic') {
        this.obj = new MonitoringObject(
          this.moduleCode,
          'module',
          null,
          this._monitoringObjectService
        );
      }

      if (this.obj) {
        return this._configService
          .init(this.moduleCode)
          .pipe(
            mergeMap(() => {
              return this.obj.get(0);
            })
          )
          .subscribe(() => {
            this.obj.initTemplate();
            this.objForm = this._formBuilder.group({});
            this.obj.bIsInitialized = true;
            this._formService.changeFormMapObj({
              frmGp: this.objForm,
              obj: this.obj,
            });
          });
      } else {
        this._configService.init(this.moduleCode);
        this.updateBreadCrumb();
      }
    });
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
    this.destroyed$.next(true);
    this.destroyed$.complete();
  }

  onEachFeatureSiteGroups(): Function {
    return (feature, layer) => {
      const popup = this._popup.setSiteGroupPopup(this.moduleCode, feature, {});
      layer.bindPopup(popup);
    };
  }

  getData(page = 1, params = {}, objectType: string) {
    if (objectType == 'sites_group') {
      this.getSitesGroups((page = page), (params = params));
    } else if (objectType == 'individual') {
      this.getIndividuals((page = page), (params = params));
    } else {
      this.getSites((page = page), (params = params));
    }
  }

  updateDataTableContent(page = 1, params = {}, _service) {
    /**
     * updateDataTableContent
     *
     * Mise à jour du contenu du composant datatable en fonction des paramètres (numéro de page, filtre)
     *  Récupère les données via _service qui correspond au serviceApi de l'objet (IndividualsService,  SitesGroupService,  SitesService)
     *  Résou les valeur des propriétés grace à la fonctionbuildObjectResolvePropertyProcessing
     *  Met à jour le composant datatable
     *
     * @param {number} page The page number to fetch.
     * @param {Object} params The parameters to pass to the service.
     * @param {_service} _service The service to use to fetch the data.
     */
    // Récupération du type d'objet
    const object_type = _service.objectObs.objectType;
    _service
      .getResolved(page, LIMIT, params)
      .subscribe((processedPaginatedData: IPaginated<any>) => {
        this.page = {
          count: processedPaginatedData.count,
          limit: processedPaginatedData.limit,
          page: processedPaginatedData.page - 1,
        };
        this.rows = processedPaginatedData.items;
        this.colsname = _service.objectObs.dataTable.colNameObj;
        this.dataTableObj[object_type].rows = processedPaginatedData.items;
        this.dataTableObj[object_type].page = {
          count: processedPaginatedData.count,
          limit: processedPaginatedData.limit,
          page: processedPaginatedData.page - 1,
        };
      });
  }

  getSitesGroups(page = 1, params = {}) {
    this.updateDataTableContent(page, params, this._sites_group_service);
    this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups(), params);
  }

  getIndividuals(page = 1, params = {}) {
    this.updateDataTableContent(page, params, this._individualService);
    this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups(), params);
  }

  getSites(page = 1, params = {}) {
    this.updateDataTableContent(page, params, this._sitesService);
    this.geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), params);
  }

  getGeometriesSite() {
    this.geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite());
  }

  onEachFeatureSite() {
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(this.moduleCode, feature, {});
      layer.bindPopup(popup);
    };
  }

  seeDetails($event) {
    // TODO: routerLink
    let objectType;
    if (this.moduleCode === 'generic') {
      if (this.activetabIndex == 1) {
        this._objService.changeObjectTypeParent(this._sitesService.objectObs);
        objectType = 'sites';
      } else {
        this._objService.changeObjectTypeParent(this._sites_group_service.objectObs);
        objectType = 'sites_group';
      }
    }

    this.router.navigate(
      [`/monitorings/object/${this.moduleCode}/`, this.currentRoute, $event[$event.id]],
      {
        queryParams: { parents_path: ['module'] },
      }
    );
  }

  editChild($event) {
    // TODO: routerLink
    const current_object = this.dataTableArray[this.activetabIndex]['objectType'];
    if (current_object == 'site') {
      this._objService.changeObjectTypeParent(this._sitesService.objectObs);
    } else if (current_object == 'individual') {
      this._objService.changeObjectTypeParent(this._individualService.objectObs);
    } else {
      this._objService.changeObjectTypeParent(this._sites_group_service.objectObs);
    }

    this._formService.changeDataSub(
      $event,
      this._sites_group_service.objectObs.objectType,
      this._sites_group_service.objectObs.endPoint
    );

    this.router.navigate([
      `/monitorings/object/${this.moduleCode}/`,
      this.currentRoute,
      $event[$event.id],
      { edit: true },
    ]);
  }

  navigateToAddChildren($event) {
    const row = $event;
    if (row) {
      row['id'] = row[row.pk];
      let queryParams = {};
      queryParams[row['pk']] = row['id'];
      const current_object = this.dataTableArray[this.activetabIndex]['objectType'];
      queryParams['parents_path'] = ['module', current_object];

      if (current_object == 'individual') {
        // Patch individual tant que la page détail des individus est générique
        queryParams['parents_path'] = ['module', 'individual'];
        this.router.navigate(
          [`/monitorings/create_object/${this.moduleCode}/`, row['object_type']],
          {
            queryParams: queryParams,
          }
        );
      } else {
        this.router.navigate(
          [`/monitorings/object/${this.moduleCode}/`, row['object_type'], 'create'],
          {
            queryParams: queryParams,
          }
        );
      }
    }
  }

  navigateToAddObj($event) {
    const type = $event;
    const queryParams = {
      parents_path: ['module'],
    };
    if (type == 'individual') {
      // Patch individual tant que la page détail des individus est générique
      queryParams['parents_path'] = ['module', 'individual'];
      this.router.navigate([`/monitorings/create_object/${this.moduleCode}/`, type], {
        queryParams: queryParams,
      });
    } else {
      this.router.navigate([`/monitorings/object/${this.moduleCode}/`, type, 'create'], {
        queryParams: queryParams,
      });
    }
  }

  onDelete(event) {
    this.currentRoute = event.objectType;
    const queryParams = { module_code: this.moduleCode };
    if (event.objectType == 'sites_group') {
      this._sites_group_service
        .delete(event.rowSelected.id_sites_group, queryParams)
        .subscribe((del) => {
          setTimeout(() => {
            this.bDeleteModalEmitter.emit(false);
            this.activetabIndex = this.getdataTableIndex(event.objectType);
            this.router.navigate(
              [`/monitorings/object/${this.moduleCode}/sites_group`, { delete: true }],
              {
                onSameUrlNavigation: 'reload',
              }
            );
            this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSiteGroups.value;
            this.updateBreadCrumb();
            this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
            this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups());
          }, 100);
        });
    } else if (event.objectType == 'individual') {
      this._individualService
        .delete(event.rowSelected.id_individual, queryParams)
        .subscribe((del) => {
          setTimeout(() => {
            this.bDeleteModalEmitter.emit(false);
            this.activetabIndex = this.getdataTableIndex(event.objectType);
            this.router.navigate(
              [`/monitorings/object/${this.moduleCode}/individual`, { delete: true }],
              {
                onSameUrlNavigation: 'reload',
              }
            );
            this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSiteGroups.value;
            this.updateBreadCrumb();
            this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
            this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups());
          }, 100);
        });
    } else {
      this._sitesService.delete(event.rowSelected.id_base_site, queryParams).subscribe((del) => {
        setTimeout(() => {
          this.bDeleteModalEmitter.emit(false);
          this.activetabIndex = this.getdataTableIndex(event.objectType);
          this.router.navigate([`/monitorings/object/${this.moduleCode}/site`, { delete: true }], {
            onSameUrlNavigation: 'reload',
          });
          this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSites.value;
          this.updateBreadCrumb();
          this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
          this.getGeometriesSite();
        }, 100);
      });
    }
  }

  onSelectedOnDataTable(data) {
    const typeObject = data[0];
    const id = data[1];
    if (typeObject == 'site') {
      this.geojsonService.selectSitesLayer(id, true);
    } else if (typeObject == 'sites_group') {
      this.geojsonService.selectSitesGroupLayer(id, true);
    }
  }

  updateBreadCrumb() {
    this._objService.changeBreadCrumb([this.breadCrumbElementBase], true);
  }

  getdataTableIndex(objetType: string) {
    return this.dataTableArray.findIndex((element) => element['objectType'] == objetType);
  }

  updateActiveTab($event) {
    this.activetabIndex = this.getdataTableIndex($event);
    if ($event == 'site') {
      this.currentRoute = 'site';
      this._location.go(`/monitorings/object/${this.moduleCode}/site`);
      this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSites.value;
      this.updateBreadCrumb();
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
      this.currentPermission.MONITORINGS_SITES.canRead ? this.getGeometriesSite() : null;
    } else if ($event == 'individual') {
      this.currentRoute = 'individual';
      this._location.go(`/monitorings/object/${this.moduleCode}/individual`);
      this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSites.value;
      this.updateBreadCrumb();
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
      this.currentPermission.MONITORINGS_SITES.canRead ? this.getGeometriesSite() : null;
    } else {
      this.currentRoute = 'sites_group';
      this._location.go(`/monitorings/object/${this.moduleCode}/sites_group`);
      this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSiteGroups.value;
      this.updateBreadCrumb();
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
      this.currentPermission.MONITORINGS_GRP_SITES.canRead
        ? this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups())
        : null;
    }
  }

  setDataTableObj(data) {
    const objTemp = {};
    for (const dataType in data) {
      if (!data[dataType].objConfig) {
        continue;
      }
      let objType = data[dataType].objConfig.objectType;
      Object.assign(objType, objTemp);
      objTemp[objType] = { columns: {}, rows: [], page: {} };
      this.config = this._configJsonService.configModuleObject(
        data[dataType].objConfig.moduleCode,
        data[dataType].objConfig.objectType
      );
      data[dataType].objConfig['config'] = this.config;
      this.dataTableArray.push(data[dataType].objConfig);
    }

    for (const dataType in data) {
      if (!data[dataType].objConfig) {
        continue;
      }
      let objType = data[dataType].objConfig.objectType;
      objTemp[objType].columns = data[dataType].objConfig.dataTable.colNameObj;
      if (objType == 'site') {
        let siteList = data[dataType].data.items;
        this.rows = siteList;
        objTemp[objType].rows = siteList;
        this.siteResolvedProperties = siteList;
      } else {
        objTemp[objType].rows = data[dataType].data.items;
      }

      objTemp[objType].page = {
        count: data[dataType].data.count,
        limit: data[dataType].data.limit,
        page: data[dataType].data.page - 1,
        total: data[dataType].data.count,
      };

      this.dataTableObj = objTemp as IDataTableObj;
    }
  }

  addChildrenVisit(event) {
    if (event.objectType == 'site') {
      this.siteSelectedId = event.rowSelected[event.rowSelected['pk']];
      if (this.moduleCode === 'generic') {
        this.getModules();
      } else {
        this.addNewVisit({ id: this.moduleCode, label: '' });
      }
    }
  }

  onSaveAddChildren($event: SelectObject) {
    this.addNewVisit($event);
  }

  getModules() {
    this._sitesService
      .getSiteModules(this.siteSelectedId)
      .pipe(takeUntil(this.destroyed$))
      .subscribe(
        (data: Module[]) => (
          (this.modules = data.map((item) => {
            return { id: item.module_code, label: item.module_label };
          })),
          this._objService.changeListOption(this.modules)
        )
      );
  }

  addNewVisit(event) {
    this.modulSelected = event;
    this._configJsonService.init(this.modulSelected.id).subscribe(() => {
      const moduleCode = this.modulSelected.id;
      const keys = Object.keys(this._configJsonService.config()[moduleCode]);
      const parents_path = ['sites_group', 'site'].filter((item) => keys.includes(item));
      this.router.navigate([`monitorings/create_object/${moduleCode}/visit`], {
        queryParams: { id_base_site: this.siteSelectedId, parents_path: parents_path },
      });
    });
  }

  initConfig(): Observable<any> {
    return this._configService.init(this.obj.moduleCode);
  }
}
