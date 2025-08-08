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
import { SelectObject } from '../../interfaces/object';
import { ConfigService } from '../../services/config.service';
import { Module } from '../../interfaces/module';
import { FormService } from '../../services/form.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { TPermission } from '../../types/permission';
import { PermissionService } from '../../services/permission.service';
import { MonitoringObject } from '../../class/monitoring-object';
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { CacheService } from '../../services/cache.service';

const LIMIT = 10;

@Component({
  selector: 'monitoring-sitesgroups-detail',
  templateUrl: './monitoring-sitesgroups-detail.component.html',
  styleUrls: ['./monitoring-sitesgroups-detail.component.css'],
})
export class MonitoringSitesgroupsDetailComponent
  extends MonitoringGeomComponent
  implements OnInit
{
  siteGroupId: number;
  sitesGroup: ISitesGroup;
  colsname: {};
  page: IPage;
  filters = {};
  @Input() bEdit: boolean;
  form: FormGroup;
  objectType: IobjObs<ISite>;
  objParent: any;

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

  obj: MonitoringObject;

  moduleCode: string;

  constructor(
    private _auth: AuthService,
    public _sitesGroupService: SitesGroupService,
    private _siteService: SitesService,
    private _objService: ObjectService,
    private router: Router,
    private _Activatedroute: ActivatedRoute,
    private _geojsonService: GeoJSONService,
    private _formBuilder: FormBuilder,
    private _configService: ConfigService,
    private _formService: FormService,
    private _permissionService: PermissionService,
    private _popup: Popup,
    private _monitoringObjectService: MonitoringObjectService,
    private _cacheService: CacheService
  ) {
    super();
    this.getAllItemsCallback = this.getSitesFromSiteGroupId;
  }

  ngOnInit() {
    this.moduleCode = this._Activatedroute.snapshot.data.detailSitesGroups.moduleCode;

    this.currentUser = this._auth.getCurrentUser();
    this.form = this._formBuilder.group({});
    this._objService.changeObjectTypeParent(this._sitesGroupService.objectObs);
    this._objService.changeObjectType(this._siteService.objectObs);
    this._configService.init(this.moduleCode).subscribe(() => {
      this.initSite();
    });
  }

  initSite() {
    this._permissionService.setPermissionMonitorings(this.moduleCode);
    this.currentPermission = this._permissionService.getPermissionUser();

    this._Activatedroute.params
      .pipe(
        map((params) => {
          this.checkEditParam = params['edit'];
          this.siteGroupId = params['id'];
          this.baseFilters = { id_sites_group: this.siteGroupId };

          // breadcrumb
          const queryParams = this._Activatedroute.snapshot.queryParams;
          this._objService.loadBreadCrumb(
            this.moduleCode,
            'sites_group',
            this.siteGroupId,
            queryParams
          );

          this.obj = new MonitoringObject(
            this.moduleCode,
            'sites_group',
            this.siteGroupId,
            this._monitoringObjectService
          );
          return this.siteGroupId as number;
        }),
        mergeMap((id: number) => {
          // this._siteService.setModuleCode(`${this.moduleCode}`);
          // this._sitesGroupService.setModuleCode(`${this.moduleCode}`);

          const fieldsConfig = this._configService.schema(this.moduleCode, 'site');
          // Récupération des sites et résolution des propriétés
          const sitedata$ = this._sitesGroupService.getSitesChildResolved(
            1,
            this.limit,
            this.baseFilters,
            fieldsConfig
          );

          return forkJoin({
            sitesGroup: this._sitesGroupService.getById(id).catch((err) => {
              if (err.status == 404) {
                this.router.navigate(['/not-found'], { skipLocationChange: true });
                return of(null);
              }
            }),
            sites: sitedata$,
            objObsSite: this._siteService.initConfig(),
            objObsSiteGp: this._sitesGroupService.initConfig(),
            obj: this.obj.get(0),
          }).pipe(
            map((data) => {
              this.obj.initTemplate();
              this.obj.bIsInitialized = true;
              if (this.moduleCode !== 'generic') {
                this._formService.changeFormMapObj({
                  frmGp: null,
                  obj: this.obj,
                });
              }
              return data;
            })
          );
        })
      )
      .subscribe((data) => {
        this._objService.changeSelectedObj(data.sitesGroup, true);
        this._objService.changeSelectedParentObj(data.sitesGroup, true);
        this.sitesGroup = data.sitesGroup;
        const sites = data.sites;

        this.page = {
          count: sites.count,
          page: sites.page,
          limit: sites.limit,
        };

        this.colsname = data.objObsSite.dataTable.colNameObj;
        this.objParent = data.objObsSiteGp;

        sites['objConfig'] = data.objObsSite;
        this.sitesGroup['objConfig'] = data.objObsSiteGp;

        this.setDataTableObj({ sites: sites, sitesGroup: this.sitesGroup });

        if (this.checkEditParam) {
          this._formService.changeDataSub(
            this.sitesGroup,
            this.objParent.objectType,
            this.objParent.endPoint
          );

          this.bEdit = true;
        }

        this.obj.bIsInitialized = true;
        this._formService.changeFormMapObj({
          frmGp: this.form,
          obj: this.obj,
        });
        this._formService.changeCurrentEditMode(this.bEdit);
      });
  }

  ngOnDestroy() {
    this._geojsonService.removeAllFeatureGroup();
    this.destroyed$.next(true);
    this.destroyed$.complete();
    this._formService.changeCurrentEditMode(false);
    this._formService.changeFormMapObj({
      frmGp: null,
      obj: {},
    });
  }

  onbEditChange(event) {
    this._formService.changeFormMapObj({
      frmGp: this.form,
      obj: this.obj,
    });
    this._formService.changeCurrentEditMode(this.bEdit);
  }

  onEachFeatureSite() {
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(this.moduleCode, feature, {
        parents_path: ['module', 'sites_group'],
      });
      layer.bindPopup(popup);
    };
  }

  onEachFeatureGroupSite() {
    return (feature, layer) => {
      const popup = this._popup.setSiteGroupPopup(this.moduleCode, feature, {
        parents_path: ['module', 'sites_group'],
      });
      layer.bindPopup(popup);
    };
  }

  getSitesFromSiteGroupId(page, params) {
    const sitesParams = { ...params, ...this.baseFilters };
    // Tableau
    const fieldsConfig = this._configService.schema(this.moduleCode, 'site');
    this._sitesGroupService
      .getSitesChildResolved(1, this.limit, this.baseFilters, fieldsConfig)
      .subscribe((data: IPaginated<ISite>) => {
        const siteList = data.items;
        this.rows = siteList;
        this.siteResolvedProperties = siteList;
        this.dataTableObj.site.rows = this.rows;
        this.dataTableObj.site.page.count = data.count;
        this.dataTableObj.site.page.limit = data.limit;
        this.dataTableObj.site.page.page = data.page - 1;
      });
    // Données carto
    this._geojsonService.getSitesGroupsGeometriesWithSites(
      this.onEachFeatureGroupSite(),
      this.onEachFeatureSite(),
      sitesParams,
      this.baseFilters
    );
  }

  seeDetails($event) {
    this._objService.changeSelectedParentObj($event);
    this._objService.changeObjectTypeParent(this._siteService.objectObs);
    this.router.navigate([`/monitorings/object/${this.moduleCode}/site/${$event.id_base_site}`], {
      queryParams: { parents_path: ['module', 'sites_group'] },
    });
  }

  editChild($event) {
    this._objService.changeSelectedParentObj($event);
    this._objService.changeObjectTypeParent(this._siteService.objectObs);
    this.router.navigate([`/monitorings/object/${this.moduleCode}/site/${$event.id_base_site}`], {
      queryParams: { parents_path: ['module', 'sites_group'] },
    });
  }

  navigateToAddObj($event) {
    const type = $event;
    const queryParams = {
      parents_path: ['module', 'sites_group'],
    };

    queryParams['id_sites_group'] = this.obj.id;
    this.router.navigate([`/monitorings/object/${this.moduleCode}/`, type, 'create'], {
      queryParams: queryParams,
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
      let config = this._configService.configModuleObject(
        this.moduleCode,
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
      let siteList = data[dataType].items;
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
    this.getSitesFromSiteGroupId(this.page.page, {});
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
    this._configService.init(this.modulSelected.id).subscribe(() => {
      const moduleCode = this.modulSelected.id;
      const keys = Object.keys(this._configService.config());
      const parents_path = ['sites_group', 'site'].filter((item) => keys.includes(item));
      this.router.navigate([`monitorings/create_object/${moduleCode}/visit`], {
        queryParams: { id_base_site: this.siteSelectedId, parents_path: parents_path },
      });
    });
  }
}
