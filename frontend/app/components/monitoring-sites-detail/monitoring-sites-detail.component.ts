import { Component, Input, OnInit, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable, ReplaySubject, forkJoin, iif, of } from 'rxjs';
import { exhaustMap, map, mergeMap, take, tap } from 'rxjs/operators';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { ModuleService } from '@geonature/services/module.service';

import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { IDataTableObj, ISite, ISiteField, ISiteType } from '../../interfaces/geom';
import { IPage, IPaginated } from '../../interfaces/page';
import { IVisit } from '../../interfaces/visit';
import { SitesGroupService, SitesService, VisitsService } from '../../services/api-geom.service';
import { GeoJSONService } from '../../services/geojson.service';
import { ObjectService } from '../../services/object.service';
import { JsonData } from '../../types/jsondata';
import { SelectObject } from '../../interfaces/object';
import { Module } from '../../interfaces/module';
import { ConfigService } from '../../services/config.service';
import { FormService } from '../../services/form.service';
import { Popup } from '../../utils/popup';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { PermissionService } from '../../services/permission.service';
import { TPermission } from '../../types/permission';
import { MonitoringObjectService } from '../../services/monitoring-object.service';

import { MonitoringObject } from '../../class/monitoring-object';

@Component({
  selector: 'monitoring-sites-detail',
  templateUrl: './monitoring-sites-detail.component.html',
  styleUrls: ['./monitoring-sites-detail.component.css'],
})
export class MonitoringSitesDetailComponent extends MonitoringGeomComponent implements OnInit {
  @Input() visits: IVisit[];
  @Input() page: IPage;
  // colsname: typeof columnNameVisit = columnNameVisit;
  @Input() bEdit: boolean;
  form: FormGroup;
  colsname: {};
  objParent: any;
  modules: SelectObject[];
  site: ISite;

  isInitialValues: boolean;
  paramToFilt: string = 'label';
  funcToFilt: Function;
  funcInitValues: Function;
  titleBtn: string = 'Choix des types de sites';
  placeholderText: string = 'Sélectionnez les types de site';
  id_sites_group: number;
  types_site: string[];
  config: JsonData;
  siteGroupIdParent: number;
  parentsPath: string[] = [];
  rows;
  dataTableObj: IDataTableObj;
  dataTableArray: {}[] = [];
  checkEditParam: boolean;

  modulSelected;
  bDeleteModalEmitter = new EventEmitter<boolean>();

  private destroyed$: ReplaySubject<boolean> = new ReplaySubject(1);

  currentUser: User;
  currentPermission: TPermission;

  obj;

  moduleCode: string;

  constructor(
    private _auth: AuthService,
    private _sitesGroupService: SitesGroupService,
    private _visits_service: VisitsService,
    private _objService: ObjectService,
    public geojsonService: GeoJSONService,
    private router: Router,
    private _Activatedroute: ActivatedRoute,
    private _formBuilder: FormBuilder,
    private _formService: FormService,
    private _configService: ConfigService,
    protected _moduleService: ModuleService,
    public siteService: SitesService,
    private _objServiceMonitoring: DataMonitoringObjectService,
    private _permissionService: PermissionService,
    private _popup: Popup,
    private _monitoringObjServiceMonitoring: MonitoringObjectService
  ) {
    super();
    this.getAllItemsCallback = this.getVisits;
  }

  ngOnInit() {
    this.moduleCode = this._Activatedroute.snapshot.data.detailSites.moduleCode;
    const idSite = this._Activatedroute.snapshot.params.id;
    this.siteService.setModuleCode(`${this.moduleCode}`);
    this._visits_service.setModuleCode(`${this.moduleCode}`);
    this._sitesGroupService.setModuleCode(`${this.moduleCode}`);
    const $configSitesGroups = this._sitesGroupService.initConfig();
    const $configSites = this.siteService.initConfig();
    const $configIndividuals = this._visits_service.initConfig();

    this.currentUser = this._auth.getCurrentUser();
    // TODO comprendre pourquoi nessaire que dans certains cas
    this.currentUser['moduleCruved'] = this._configService.moduleCruved(this.moduleCode);
    this.funcInitValues = this.initValueToSend.bind(this);
    this.funcToFilt = this.partialfuncToFilt.bind(this);
    this.form = this._formBuilder.group({});

    // breadcrumb
    const queryParams = this._Activatedroute.snapshot.queryParams;
    this._objService.loadBreadCrumb(this.moduleCode, 'site', idSite, queryParams);

    forkJoin([
      this._configService.init(this.moduleCode),
      $configSitesGroups,
      $configSites,
      $configIndividuals,
    ]).subscribe(() => {
      this.initSiteVisit();
    });
  }

  initSiteVisit() {
    this._permissionService.setPermissionMonitorings(this.moduleCode);
    this.currentPermission = this._permissionService.getPermissionUser();

    this._Activatedroute.params
      .pipe(
        map((params) => {
          this.checkEditParam = params['edit'];
          this.parentsPath =
            this._Activatedroute.snapshot.queryParamMap.getAll('parents_path') || [];
          this.obj = new MonitoringObject(
            this.moduleCode,
            'site',
            params['id'],
            this._monitoringObjServiceMonitoring
          );
          return params['id'] as number;
        }),
        tap((id: number) => {
          this.geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
            id_base_site: id,
          });
        }),
        mergeMap((id: number) => {
          return forkJoin({
            site: this.siteService.getById(id).catch((err) => {
              if (err.status == 404) {
                this.router.navigate(['/not-found'], { skipLocationChange: true });
                return of(null);
              }
            }),
            visits: this._visits_service.getResolved(1, this.limit, {
              id_base_site: id,
            }),
          }).pipe(
            map((data) => {
              return data;
            })
          );
        }),
        exhaustMap((data) => {
          return forkJoin({
            objObsSite: this.siteService.initConfig(),
            objObsVisit: this._visits_service.initConfig(),
            obj: this.obj.get(0),
          }).pipe(
            tap((objConfig) => (this.objParent = objConfig.objObsSite)),
            map((objConfig) => {
              return { data, objConfig: objConfig };
            })
          );
        }),
        mergeMap(({ data, objConfig }) => {
          return of({
            site: data.site,
            visits: data.visits,
            objConfig: objConfig,
          });
        }),
        mergeMap((data) => {
          if (this.parentsPath.includes('sites_group')) {
            this.siteGroupIdParent = data.site.id_sites_group;
          }
          return of(data);
        })
      )
      .subscribe((data) => {
        this.obj.initTemplate();
        this.obj.bIsInitialized = true;
        if (this.moduleCode !== 'generic') {
          this._formService.changeFormMapObj({
            frmGp: null,
            obj: this.obj,
          });
        }
        this.site = data.site;
        this.types_site = data.site['types_site'];
        this.visits = data.visits.items;
        this.page = {
          page: data.visits.page - 1,
          count: data.visits.count,
          limit: data.visits.limit,
        };

        this.baseFilters = { id_base_site: this.site.id_base_site };
        this.colsname = data.objConfig.objObsVisit.dataTable.colNameObj;

        this.addSpecificConfig();

        const { objConfig, ...dataonlyObjConfigAndObj } = data;

        dataonlyObjConfigAndObj.site['objConfig'] = objConfig.objObsSite;
        dataonlyObjConfigAndObj.visits['objConfig'] = objConfig.objObsVisit;
        this.setDataTableObj(dataonlyObjConfigAndObj);

        if (this.checkEditParam) {
          this._formService.changeDataSub(
            this.site,
            this.siteService.objectObs.objectType,
            this.siteService.objectObs.endPoint,
            this.moduleCode
          );

          this.bEdit = true;
          this._formService.changeCurrentEditMode(this.bEdit);
        }
      });
    this.isInitialValues = true;
  }

  onEachFeatureSite() {
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(this.moduleCode, feature, {});
      layer.bindPopup(popup);
    };
  }

  getVisits(page: number, filters: JsonData) {
    const queryParams = { ...filters, ...{ id_base_site: this.site.id_base_site } };
    this._visits_service
      .getResolved(page, this.limit, queryParams)
      .subscribe((visits: IPaginated<IVisit>) => this.setVisits(visits));
  }

  setVisits(visits) {
    this.rows = visits.items;
    this.dataTableObj.visit.rows = this.rows;
    this.dataTableObj.visit.page.count = visits.count;
    this.dataTableObj.visit.page.limit = visits.limit;
    this.dataTableObj.visit.page.page = visits.page - 1;
  }

  seeDetails($event) {
    this.router.navigate(
      [`/monitorings/object/${$event.module.module_code}/visit/${$event.id_base_visit}`],
      {
        queryParams: { parents_path: ['module', 'site'] },
      }
    );
  }

  getModules() {
    if (this.moduleCode === 'generic') {
      this.siteService.getSiteModules(this.site.id_base_site).subscribe(
        (data: Module[]) =>
          (this.modules = data.map((item) => {
            return { id: item.module_code, label: item.module_label };
          }))
      );
    } else {
      this.addNewVisit({ id: this.moduleCode, label: '' });
    }
  }

  addNewVisit($event: SelectObject) {
    const moduleCode = $event.id;
    //create_object/cheveches_sites_group/visit?id_base_site=47
    this._configService.init(moduleCode).subscribe(() => {
      const keys = Object.keys(this._configService.config()[moduleCode]);
      const parents_path = ['sites_group', 'site'].filter((item) => keys.includes(item));
      this.router.navigate([`monitorings/create_object/${moduleCode}/visit`], {
        queryParams: { id_base_site: this.site.id_base_site, parents_path: parents_path },
      });
    });
  }

  editChild($event) {
    this.router.navigate([
      `monitorings/object/${$event.module.module_code}/visit/${$event.id_base_visit}`,
      { edit: true },
    ]);
  }

  // TODO: voir s'il faut pouvoir supprimer les visites depuis l'entrée par sites
  onDelete($event) {
    this._objServiceMonitoring
      .deleteObject($event.rowSelected.module.module_code, $event.objectType, $event.rowSelected.id)
      .subscribe((del) => {
        this.bDeleteModalEmitter.emit(false);
        this.initSiteVisit();
      });
  }

  partialfuncToFilt(
    pageNumber: number,
    limit: number,
    valueToFilter: string
  ): Observable<IPaginated<ISiteType>> {
    return this.siteService.getTypeSites(pageNumber, limit, {
      label_fr: valueToFilter,
      sort_dir: 'desc',
    });
  }

  onSendConfig(config: JsonData): void {
    this.config = this.addTypeSiteListIds(config);
    this.updateForm();
  }

  addTypeSiteListIds(config: JsonData): JsonData {
    if (config && config.length != 0) {
      config.types_site = [];
      for (const key in config) {
        if ('id_nomenclature_type_site' in config[key]) {
          config.types_site.push(config[key]['id_nomenclature_type_site']);
        }
      }
    }
    return config;
  }

  addSpecificConfig() {
    this.objParent['template_specific'] = {};
    this.objParent['template_specific'] = this._monitoringObjServiceMonitoring
      .configService()
      .addSpecificConfig(this.types_site);
  }

  initValueToSend() {
    this.initSiteVisit();
    return this.types_site;
  }

  updateForm() {
    this.site.specific = {};
    this.site.dataComplement = {};
    for (const key in this.config) {
      if (this.config[key].config != undefined) {
        if (Object.keys(this.config[key].config).length !== 0) {
          Object.assign(this.site.specific, this.config[key].config.specific);
        }
      }
    }
    const specificData = {};
    for (const k in this.site.data) this.site[k] = this.site.data[k];
    for (const k in this.site.data) specificData[k] = this.site.data[k];
    this.site.types_site = this.config.types_site;
    Object.assign(this.site.dataComplement, this.config);
    this._formService.updateSpecificForm(this.site, specificData);
  }

  onbEditChange(event) {
    this._formService.changeFormMapObj({
      frmGp: this.form,
      obj: this.obj,
    });
    this._formService.changeCurrentEditMode(this.bEdit);
  }

  setDataTableObj(data) {
    const objTemp = {};
    for (const dataType in data) {
      let objType = data[dataType].objConfig.objectType;
      if (objType != 'visit') {
        continue;
      }
      Object.assign(objType, objTemp);
      objTemp[objType] = { columns: {}, rows: [], page: {} };
      let config = this._configService.configModuleObject(
        data[dataType].objConfig.moduleCode,
        data[dataType].objConfig.objectType
      );
      data[dataType].objConfig['config'] = config;
      this.dataTableArray.push(data[dataType].objConfig);
    }

    for (const dataType in data) {
      let objType = data[dataType].objConfig.objectType;
      if (objType != 'visit') {
        continue;
      }
      objTemp[objType].columns = data[dataType].objConfig.dataTable.colNameObj;
      objTemp[objType].rows = data[dataType].items;

      objTemp[objType].page = {
        count: data[dataType].count,
        limit: data[dataType].limit,
        page: data[dataType].page - 1,
        total: data[dataType].count,
      };

      this.dataTableObj = objTemp as IDataTableObj;
    }
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
    this._formService.changeCurrentEditMode(false);
    this._formService.changeFormMapObj({
      frmGp: null,
      obj: {},
    });
    this.destroyed$.next(true);
    this.destroyed$.complete();
  }
}
