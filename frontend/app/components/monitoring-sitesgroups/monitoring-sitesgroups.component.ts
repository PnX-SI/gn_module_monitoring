import { Location } from '@angular/common';
import { Component, EventEmitter, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { MonitoringObject } from '../../class/monitoring-object';
import { ISitesGroup } from '../../interfaces/geom';
import { Module } from '../../interfaces/module';
import { SelectObject } from '../../interfaces/object';
import { IobjObs } from '../../interfaces/objObs';
import { IPage, IPaginated } from '../../interfaces/page';

import {
  IndividualsService,
  ModuleService,
  SitesGroupService,
  SitesService,
} from '../../services/api-geom.service';
import { ConfigService } from '../../services/config.service';
import { FormService } from '../../services/form.service';
import { GeoJSONService } from '../../services/geojson.service';
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ObjectService } from '../../services/object.service';
import { TPermission } from '../../types/permission';
import { Popup } from '../../utils/popup';

const LIMIT = 10;

import { ReplaySubject } from 'rxjs';
import { mergeMap, takeUntil } from 'rxjs/operators';
import { PermissionService } from '../../services/permission.service';
import { ObjectType } from '../../enum/objecttype';
import { resolveObjectProperties } from '../../utils/utils';
import { CacheService } from '../../services/cache.service';

@Component({
  selector: 'monitoring-sitesgroups',
  templateUrl: './monitoring-sitesgroups.component.html',
  styleUrls: ['./monitoring-sitesgroups.component.css'],
})
export class MonitoringSitesGroupsComponent extends MonitoringGeomComponent implements OnInit {
  obj;
  resolvedObj;
  public bDeleteModalEmitter: EventEmitter<boolean> = new EventEmitter<boolean>();
  public page: IPage;

  colsname: {};
  objectType: IobjObs<ISitesGroup>;
  objForm: FormGroup;
  objInitForm: Object = {};
  rows;
  dataTableConfig: {}[] = [];
  activetabIndex: number;
  currentRoute: string;

  modules: SelectObject[];

  private destroyed$: ReplaySubject<boolean> = new ReplaySubject(1);

  siteResolvedProperties;

  currentUser: User;
  currentPermission: TPermission;

  public moduleCode: string;

  public bEdit: boolean = false;
  public bIsInitialized: boolean;
  // TODO: move to a common file
  private childTypes: { [index: string]: string } = {
    site: 'visit',
    sites_group: 'site',
    individual: 'marking',
  };

  constructor(
    private _auth: AuthService,
    private _sites_group_service: SitesGroupService,
    private _sitesService: SitesService,
    private _individualService: IndividualsService,
    public geojsonService: GeoJSONService,
    private router: Router,
    private _objService: ObjectService,
    private _formBuilder: FormBuilder,
    private _Activatedroute: ActivatedRoute, // private _routingService: RoutingService
    private _formService: FormService,
    private _location: Location,
    private _popup: Popup,
    public _permissionService: PermissionService,
    private _moduleService: ModuleService,
    private _cacheService: CacheService
  ) {
    super(_permissionService);
    this.getAllItemsCallback = this.getData;
  }

  ngOnInit() {
    this.moduleCode = this._configServiceG.moduleCode();
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
    this.initObject();
  }

  initObject() {
    this._Activatedroute.data.subscribe(({ data }) => {
      let currentData;
      switch (data.route) {
        case ObjectType.site:
          currentData = data.sites;
          break;
        case ObjectType.individual:
          currentData = data.individuals;
          break;
        default:
          currentData = data.sites_groups;
          break;
      }
      this.page = {
        count: currentData.count,
        limit: currentData.limit,
        page: currentData.page - 1,
      };

      this.currentUser = this._auth.getCurrentUser();
      this.currentPermission = data.permission;
      this.currentRoute = data.route;

      this.geojsonService.setModuleCode(this.moduleCode);

      // breadcrumb
      const queryParams = this._Activatedroute.snapshot.queryParams;
      this._objService.loadBreadCrumb(this.moduleCode, 'module', null, queryParams);

      let dataToTable = {};
      for (const objType of Object.keys(this._configServiceG.config()['tree']['module'])) {
        dataToTable[objType] = {
          data: data[`${objType}s`],
          objType: objType,
          childType: this.childTypes[objType],
        };
      }
      this.setDataTableObjData(dataToTable, this.moduleCode, [
        ObjectType.site,
        ObjectType.individual,
        ObjectType.sites_group,
      ]);

      // Indentify active tab
      this.activetabIndex = this.getdataTableIndex(data.route);

      if (data.route == ObjectType.site) {
        this.currentPermission.site.R > 0 ? this.getGeometriesSite() : null;
      } else {
        this.currentPermission.sites_group.R > 0
          ? this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups())
          : null;
      }

      if (this.moduleCode != 'generic') {
        // this._moduleService.getModulebyCode(this.moduleCode).subscribe((data) => {
        this._moduleService.getById(99, this.moduleCode).subscribe((data) => {
          this.obj = data;
          this.resolvedObj = resolveObjectProperties(
            this.obj,
            this._configServiceG.config()['module']['fields'],
            this._configServiceG,
            this._cacheService
          );
          this.setTemplateData('module');

          this.objForm = this._formBuilder.group({});
          this.bIsInitialized = true;
        });
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
    if (objectType == ObjectType.sites_group) {
      this.getSitesGroups((page = page), (params = params));
    } else if (objectType == ObjectType.individual) {
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
    const object_type: ObjectType = _service.objectObs.objectType;
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
        this.dataTableObjData[object_type].rows = processedPaginatedData.items;
        this.dataTableObjData[object_type].page = {
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
    this.router.navigate(
      [`/monitorings/object/${this.moduleCode}/`, this.currentRoute, $event[$event.id]],
      {
        queryParams: { parents_path: ['module'] },
      }
    );
  }

  editChild($event) {
    // TODO: routerLink
    const queryParams = {
      parents_path: ['module'],
      edit: true,
    };
    this.router.navigate([
      `/monitorings/object/${this.moduleCode}/`,
      this.currentRoute,
      $event[$event.id],
      queryParams,
    ]);
  }

  navigateToAddChildren($event) {
    const row = $event;
    if (row) {
      row['id'] = row[row.pk];
      let queryParams = {};
      queryParams[row['pk']] = row['id'];
      const current_object = this.dataTableConfig[this.activetabIndex]['objectType'];
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

  getdataTableIndex(objetType: string) {
    return this.dataTableConfig.findIndex((element) => element['objectType'] == objetType);
  }

  updateActiveTab($event) {
    this.activetabIndex = this.getdataTableIndex($event);
    if ($event == 'site') {
      this.currentRoute = 'site';
      this._location.go(`/monitorings/object/${this.moduleCode}/site`);
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
      this.currentPermission.site.R > 0 ? this.getGeometriesSite() : null;
    } else if ($event == 'individual') {
      this.currentRoute = 'individual';
      this._location.go(`/monitorings/object/${this.moduleCode}/individual`);
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
      this.currentPermission.site.R > 0 ? this.getGeometriesSite() : null;
    } else {
      this.currentRoute = 'sites_group';
      this._location.go(`/monitorings/object/${this.moduleCode}/sites_group`);
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
      this.currentPermission.sites_group.R > 0
        ? this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups())
        : null;
    }
  }

  addChildrenVisit(event) {
    if (event.objectType == 'site') {
      const siteId = event.rowSelected[event.rowSelected['pk']];
      if (this.moduleCode === 'generic') {
        this.getModules(siteId);
      } else {
        this.addNewVisit(siteId);
      }
    }
  }

  onSaveAddChildren($event: SelectObject) {
    this.addNewVisit($event);
  }

  getModules(siteId: number) {
    this._sitesService
      .getSiteModules(siteId, this.moduleCode)
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

  addNewVisit(idSite) {
    const keys = Object.keys(this._configServiceG.config());
    const parents_path = ['sites_group', 'site'].filter((item) => keys.includes(item));
    this.router.navigate([`monitorings/create_object/${this.moduleCode}/visit`], {
      queryParams: { id_base_site: idSite, parents_path: parents_path },
    });
  }
}
