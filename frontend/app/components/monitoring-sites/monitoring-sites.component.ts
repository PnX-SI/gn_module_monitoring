import { Component, OnInit, Input, EventEmitter } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ReplaySubject, forkJoin, of } from 'rxjs';
import { tap, map, mergeMap, takeUntil, switchMap, concatMap } from 'rxjs/operators';
import * as L from 'leaflet';
import { IDataTableObj, ISite, ISiteField, ISitesGroup } from '../../interfaces/geom';
import { IPage, IPaginated } from '../../interfaces/page';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { GeoJSONService } from '../../services/geojson.service';
import { FormGroup, FormBuilder } from '@angular/forms';
import { SitesService, SitesGroupService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { IobjObs } from '../../interfaces/objObs';
import { IBreadCrumb, SelectObject } from '../../interfaces/object';
import { breadCrumbElementBase } from '../breadcrumbs/breadcrumbs.component';
import { ConfigJsonService } from '../../services/config-json.service';
import { ConfigService } from '../../services/config.service';
import { Module } from '../../interfaces/module';
import { FormService } from '../../services/form.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { TPermission } from '../../types/permission';
import { PermissionService } from '../../services/permission.service';

const LIMIT = 10;

@Component({
  selector: 'monitoring-sites',
  templateUrl: './monitoring-sites.component.html',
  styleUrls: ['./monitoring-sites.component.css'],
})
export class MonitoringSitesComponent extends MonitoringGeomComponent implements OnInit {
  siteGroupId: number;
  sites: ISite[];
  sitesGroup: ISitesGroup;
  colsname: {};
  page: IPage;
  filters = {};
  @Input() bEdit: boolean;
  objForm: { static: FormGroup };
  objectType: IobjObs<ISite>;
  objParent: any;
  breadCrumbElemnt: IBreadCrumb = { label: 'Groupe de site', description: '' };
  breadCrumbElementBase: IBreadCrumb = breadCrumbElementBase;
  breadCrumbList: IBreadCrumb[] = [];

  modules: SelectObject[];
  modulSelected;
  siteSelectedId: number;
  rows;
  siteResolvedProperties;
  dataTableObj: IDataTableObj;
  dataTableArray: {}[] = [];
  checkEditParam: boolean;

  private destroyed$: ReplaySubject<boolean> = new ReplaySubject(1);

  bDeleteModalEmitter = new EventEmitter<boolean>();

  currentUser: User;
  currentPermission: TPermission;

  constructor(
    private _auth: AuthService,
    public _sitesGroupService: SitesGroupService,
    private _siteService: SitesService,
    private _objService: ObjectService,
    private router: Router,
    private _Activatedroute: ActivatedRoute,
    private _geojsonService: GeoJSONService,
    private _configJsonService: ConfigJsonService,
    private _formBuilder: FormBuilder,
    private _configService: ConfigService,
    private _formService: FormService,
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _permissionService: PermissionService,
    private _popup: Popup
  ) {
    super();
    this.getAllItemsCallback = this.getSitesFromSiteGroupId;
  }

  ngOnInit() {
    this.currentUser = this._auth.getCurrentUser();
    this.objForm = { static: this._formBuilder.group({}) };
    // this._sitesGroupService.init()
    this._objService.changeObjectTypeParent(this._sitesGroupService.objectObs);
    this._objService.changeObjectType(this._siteService.objectObs);
    this.initSite();
  }

  initSite() {
    const $getPermissionMonitoring = this._dataMonitoringObjectService.getCruvedMonitoring();
    const $permissionUserObject = this._permissionService.currentPermissionObj;
    $getPermissionMonitoring
      .pipe(
        map((listObjectCruved: Object) => {
          this._permissionService.setPermissionMonitorings(listObjectCruved);
        }),
        concatMap(() =>
          $permissionUserObject.pipe(
            map((permissionObject: TPermission) => (this.currentPermission = permissionObject))
          )
        ),
        concatMap(() =>
          this._Activatedroute.params.pipe(
            map((params) => {
              this.checkEditParam = params['edit'];
              return params['id'] as number;
            }),
            mergeMap((id: number) => {
              return forkJoin({
                sitesGroup: this._sitesGroupService.getById(id).catch((err) => {
                  if (err.status == 404) {
                    this.router.navigate(['/not-found'], { skipLocationChange: true });
                    return of(null);
                  }
                }),
                sites: this._sitesGroupService.getSitesChild(1, this.limit, {
                  id_sites_group: id,
                }),
              }).pipe(
                map((data) => {
                  return data;
                })
              );
            }),
            tap((data) => {
              data.sitesGroup.is_geom_from_child
                ? this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
                  id_sites_group: data.sitesGroup.id_sites_group,
                })
                : this._geojsonService.setGeomSiteGroupFromExistingObject(data.sitesGroup.geometry);
            }),
            mergeMap((data) => {
              return forkJoin({
                objObsSite: this._siteService.initConfig(),
                objObsSiteGp: this._sitesGroupService.initConfig(),
              }).pipe(
                map((objObs) => {
                  return { data, objectObs: objObs };
                })
              );
            })
          )
        )
      )
      .subscribe(({ data, objectObs }) => {
        this._objService.changeSelectedObj(data.sitesGroup, true);
        this._objService.changeSelectedParentObj(data.sitesGroup, true);
        this.sitesGroup = data.sitesGroup;
        this.sites = data.sites.items;
        this.page = {
          count: data.sites.count,
          page: data.sites.page,
          limit: data.sites.limit,
        };

        this.baseFilters = { id_sites_group: this.sitesGroup.id_sites_group };
        this.colsname = objectObs.objObsSite.dataTable.colNameObj;
        this.objParent = objectObs.objObsSiteGp;

        data.sites['objConfig'] = objectObs.objObsSite;
        data.sitesGroup['objConfig'] = objectObs.objObsSiteGp;
        this.updateBreadCrumb(data.sitesGroup);
        this.setDataTableObj(data);
        if (this.checkEditParam) {
          this._formService.changeDataSub(
            this.sitesGroup,
            this.objParent.objectType,
            this.objParent.endPoint
          );

          this.bEdit = true;
        }
      });
  }
  ngOnDestroy() {
    this._geojsonService.removeAllFeatureGroup();
    this.destroyed$.next(true);
    this.destroyed$.complete();
  }

  onEachFeatureSite() {
    const baseUrl = this.router.url + '/site';
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(feature);
      layer.bindPopup(popup);
    };
  }

  getSitesFromSiteGroupId(page, params) {
    this._sitesGroupService
      .getSitesChild(page, LIMIT, params)
      .subscribe((data: IPaginated<ISite>) => {
        let siteList = this._siteService.formatLabelTypesSite(data.items);
        this.rows = siteList;
        this.siteResolvedProperties = siteList;
        this.dataTableObj.site.rows = this.rows;
        this.dataTableObj.site.page.count = data.count;
        this.dataTableObj.site.page.limit = data.limit;
        this.dataTableObj.site.page.page = data.page - 1;
      });
    this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), params);
  }

  seeDetails($event) {
    this._objService.changeSelectedParentObj($event);
    this._objService.changeObjectTypeParent(this._siteService.objectObs);
    this.router.navigate([`site/${$event.id_base_site}`], {
      relativeTo: this._Activatedroute,
    });
  }

  editChild($event) {
    this._objService.changeSelectedParentObj($event);
    this._objService.changeObjectTypeParent(this._siteService.objectObs);
    this.router.navigate([`site/${$event.id_base_site}`, { edit: true }], {
      relativeTo: this._Activatedroute,
    });
  }

  onDelete(event) {
    this._siteService.delete(event.rowSelected.id_base_site).subscribe((del) => {
      setTimeout(() => {
        this.bDeleteModalEmitter.emit(false);
        this.initSite();
      }, 100);
    });
  }

  updateBreadCrumb(sitesGroup) {
    this.breadCrumbElemnt.description = sitesGroup.sites_group_name;
    this.breadCrumbElemnt.label = 'Groupe de site';
    this.breadCrumbElemnt['id'] = sitesGroup.id_sites_group;
    this.breadCrumbElemnt['objectType'] =
      this._sitesGroupService.objectObs.objectType || 'sites_group';
    this.breadCrumbElemnt['url'] = [
      this.breadCrumbElementBase.url,
      this.breadCrumbElemnt.id?.toString(),
    ].join('/');

    this.breadCrumbList = [this.breadCrumbElementBase, this.breadCrumbElemnt];
    this._objService.changeBreadCrumb(this.breadCrumbList, true);
  }

  onObjChanged($event) {
    if ($event == 'deleted') {
      return;
    }
    this._geojsonService.removeAllFeatureGroup();
    this.initSite();
  }

  setDataTableObj(data) {
    const objTemp = {};
    for (const dataType in data) {
      let objType = data[dataType].objConfig.objectType;
      if (objType == 'sites_group') {
        continue;
      }
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
      if (objType == 'sites_group') {
        continue;
      }
      objTemp[objType].columns = data[dataType].objConfig.dataTable.colNameObj;
      let siteList = this._siteService.formatLabelTypesSite(data[dataType].items);
      this.rows = siteList;
      objTemp[objType].rows = siteList;
      this.siteResolvedProperties = siteList;

      objTemp[objType].page = {
        count: data[dataType].count,
        limit: data[dataType].limit,
        page: data[dataType].page - 1,
        total: data[dataType].count,
      };

      this.dataTableObj = objTemp as IDataTableObj;
    }
  }

  onAddChildren(event) {
    if (event.objectType == 'site') {
      this.siteSelectedId = event.rowSelected[event.rowSelected['pk']];
      this.getModules();
    }
  }

  onSaveAddChildren($event: SelectObject) {
    this.addNewVisit($event);
  }
  getModules() {
    this._siteService
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
      const parent_paths = ['sites_group', 'site'].filter((item) => keys.includes(item));
      this.router.navigate([`monitorings/create_object/${moduleCode}/visit`], {
        queryParams: { id_base_site: this.siteSelectedId, parents_path: parent_paths },
      });
    });
  }
}
