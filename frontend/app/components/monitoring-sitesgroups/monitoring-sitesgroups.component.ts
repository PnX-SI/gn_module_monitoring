import { Component, OnInit, Input, EventEmitter } from '@angular/core';
import { SitesGroupService, SitesService } from '../../services/api-geom.service';
import { IPaginated, IPage } from '../../interfaces/page';
import { Router, ActivatedRoute } from '@angular/router';
import { IDataTableObj, ISite, ISitesGroup } from '../../interfaces/geom';
import { GeoJSONService } from '../../services/geojson.service';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { ObjectService } from '../../services/object.service';
import { FormGroup, FormBuilder } from '@angular/forms';
import { IobjObs } from '../../interfaces/objObs';
import { ConfigJsonService } from '../../services/config-json.service';
import { IBreadCrumb, SelectObject } from '../../interfaces/object';
import { FormService } from '../../services/form.service';
import { Location } from '@angular/common';
import { breadCrumbBase } from '../../class/breadCrumb';
import { Module } from '../../interfaces/module';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { TPermission } from '../../types/permission';
import { MonitoringObject } from '../../class/monitoring-object';
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ConfigService } from '../../services/config.service';

const LIMIT = 10;

import { Observable, of, forkJoin, ReplaySubject } from 'rxjs';
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

@Component({
  selector: 'monitoring-sitesgroups',
  templateUrl: './monitoring-sitesgroups.component.html',
  styleUrls: ['./monitoring-sitesgroups.component.css'],
})
export class MonitoringSitesGroupsComponent extends MonitoringGeomComponent implements OnInit {
  page: IPage;
  sitesGroups: ISitesGroup[];

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

  constructor(
    private _auth: AuthService,
    private _sites_group_service: SitesGroupService,
    private _sitesService: SitesService,
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
    private _configService: ConfigService
  ) {
    super();
    this.getAllItemsCallback = this.getSitesOrSitesGroups; //[this.getSitesGroups, this.getSites];
  }

  ngOnInit() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
    this.initSiteGroup();
    this._objService.changeSelectedObj({}, true);
    // this._formService.changeFormMapObj({frmGp: this._formBuilder.group({}),bEdit:false, objForm: {}})
  }

  initSiteGroup() {
    this._objService.changeObjectTypeParent(this._sites_group_service.objectObs);
    this._objService.changeObjectType(this._sites_group_service.objectObs);

    this._Activatedroute.data.subscribe(({ data }) => {
      this.moduleCode = data.moduleCode;
      this.currentUser = this._auth.getCurrentUser();
      this.currentUser['moduleCruved'] = this._configService.moduleCruved(this.moduleCode);

      this.currentPermission = data.permission;
      this.page = {
        count: data.sitesGroups.data.count,
        limit: data.sitesGroups.data.limit,
        page: data.sitesGroups.data.page - 1,
      };
      this.sitesGroups = data.sitesGroups.data.items;
      // this.columns = [data.sitesGroups.data.items, data.sites.data.items]
      this.colsname = data.sitesGroups.objConfig.dataTable.colNameObj;
      this.currentRoute = data.route;
      if (data.route == 'site') {
        this.activetabIndex = 1;
        this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSites.value;
        this.currentPermission.MONITORINGS_SITES.canRead ? this.getGeometriesSite() : null;
      } else {
        this.activetabIndex = 0;
        this.currentPermission.MONITORINGS_GRP_SITES.canRead
          ? this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups())
          : null;
      }
      const { route, permission, moduleCode, ...dataToTable } = data;

      this.setDataTableObj(dataToTable);

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
              return this.obj.get(1);
            })
          )
          .subscribe(() => {
            this.obj.initTemplate();
            this.objForm = this._formBuilder.group({});
            this.obj.bIsInitialized = true;
            this._formService.changeFormMapObj({
              frmGp: this.objForm,
              bEdit: false,
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

  getSitesOrSitesGroups(page = 1, params = {}, siteOrSiteGroups: string) {
    if (siteOrSiteGroups == 'sites_group') {
      this.getSitesGroups((page = page), (params = params));
    } else {
      this.getSites((page = page), (params = params));
    }
  }

  getSitesGroups(page = 1, params = {}) {
    this._sites_group_service
      .get(page, LIMIT, params)
      .subscribe((data: IPaginated<ISitesGroup>) => {
        this.page = {
          count: data.count,
          limit: data.limit,
          page: data.page - 1,
        };
        this.sitesGroups = data.items;
        this.rows = data.items;
        this.colsname = this._sites_group_service.objectObs.dataTable.colNameObj;
        this.dataTableObj.sites_group.rows = data.items;
        this.dataTableObj.sites_group.page.count = data.count;
        this.dataTableObj.sites_group.page.limit = data.limit;
        this.dataTableObj.sites_group.page.page = data.page - 1;
      });
    this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups(), params);
  }

  getSites(page = 1, params = {}) {
    this._sitesService.get(page, LIMIT, params).subscribe((data: IPaginated<ISite>) => {
      this.colsname = this._sitesService.objectObs.dataTable.colNameObj;
      let siteList = this._sitesService.formatLabelTypesSite(data.items);
      this.rows = siteList;
      const siteListResolvedProp = this._sitesService.formatLabelObservers(siteList);
      this.siteResolvedProperties = siteListResolvedProp;
      this.dataTableObj.site.rows = this.siteResolvedProperties;
      this.dataTableObj.site.page.count = data.count;
      this.dataTableObj.site.page.limit = data.limit;
      this.dataTableObj.site.page.page = data.page - 1;
    });
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
    if (this.activetabIndex == 1) {
      this._objService.changeObjectTypeParent(this._sitesService.objectObs);
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
      queryParams['parents_path'] = ['module', 'sites_group'];

      this.router.navigate(
        [`/monitorings/object/${this.moduleCode}/`, row['object_type'], 'create'],
        {
          queryParams: queryParams,
        }
      );
    }
  }

  navigateToAddObj($event) {
    const type = $event;
    const queryParams = {
      parents_path: ['module'],
    };
    this.router.navigate([`/monitorings/object/${this.moduleCode}/`, type, 'create'], {
      queryParams: queryParams,
    });
  }

  onDelete(event) {
    if (event.objectType == 'sites_group') {
      this._sites_group_service.delete(event.rowSelected.id_sites_group).subscribe((del) => {
        setTimeout(() => {
          this.bDeleteModalEmitter.emit(false);
          this.activetabIndex = 0;
          this.currentRoute = 'sites_group';
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
    } else {
      this._sitesService.delete(event.rowSelected.id_base_site).subscribe((del) => {
        setTimeout(() => {
          this.bDeleteModalEmitter.emit(false);
          this.activetabIndex = 1;
          this.currentRoute = 'site';
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

  updateActiveTab($event) {
    if ($event == 'site') {
      this.activetabIndex = 1;
      this.currentRoute = 'site';
      this._location.go(`/monitorings/object/${this.moduleCode}/site`);
      this.breadCrumbElementBase = breadCrumbBase.baseBreadCrumbSites.value;
      this.updateBreadCrumb();
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
      this.currentPermission.MONITORINGS_SITES.canRead ? this.getGeometriesSite() : null;
    } else {
      this.activetabIndex = 0;
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
      let objType = data[dataType].objConfig.objectType;
      Object.assign(objType, objTemp);
      objTemp[objType] = { columns: {}, rows: [], page: {} };
      let config = this._configJsonService.configModuleObject(
        data[dataType].objConfig.moduleCode,
        data[dataType].objConfig.objectType
      );
      data[dataType].objConfig['config'] = config;
      this.dataTableArray.push(data[dataType].objConfig);
    }

    for (const dataType in data) {
      let objType = data[dataType].objConfig.objectType;
      objTemp[objType].columns = data[dataType].objConfig.dataTable.colNameObj;
      if (objType == 'site') {
        let siteList = this._sitesService.formatLabelTypesSite(data[dataType].data.items);
        this.rows = siteList;
        const siteListResolvedProp = this._sitesService.formatLabelObservers(siteList);
        objTemp[objType].rows = siteListResolvedProp;
        this.siteResolvedProperties = siteListResolvedProp;
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
