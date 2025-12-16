import { Component, Input, OnInit, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ReplaySubject, forkJoin, of } from 'rxjs';
import { mergeMap, map } from 'rxjs/operators';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { ModuleService } from '@geonature/services/module.service';

import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { IdataTableObjData, ISite, ISiteField, ISiteType } from '../../interfaces/geom';
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
  @Input() bEdit: boolean;
  form: FormGroup;
  objParent: any;
  modules: SelectObject[];
  site: ISite;

  config: JsonData;
  siteGroupIdParent: number;
  parentsPath: string[] = [];
  rows;
  dataTableConfig: {}[] = [];
  checkEditParam: boolean;

  bDeleteModalEmitter = new EventEmitter<boolean>();

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
        mergeMap((params) => {
          const siteId = params['id'] as number;
          this.checkEditParam = params['edit'];

          this.parentsPath =
            this._Activatedroute.snapshot.queryParamMap.getAll('parents_path') || [];
          this.obj = new MonitoringObject(
            this.moduleCode,
            'site',
            params['id'],
            this._monitoringObjServiceMonitoring
          );

          // Récupération et affichage de la géométrie du site
          this.geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
            id_base_site: siteId,
          });

          // Récupération des données et des configurations
          //  pour le site et les visites associées
          return forkJoin({
            site: this.siteService.getById(siteId, this.moduleCode).catch((err) => {
              if (err.status == 404) {
                this.router.navigate(['/not-found'], { skipLocationChange: true });
                return of(null);
              }
            }),
            visits: this._visits_service.getResolved(1, this.limit, {
              id_base_site: siteId,
            }),
            objObsSite: this.siteService.initConfig(),
            objObsVisit: this._visits_service.initConfig(),
            obj: this.obj.get(0),
          });
        })
      )
      .subscribe((data) => {
        this.objParent = data.objObsSite;
        this.obj.initTemplate();
        this.site = data.site;

        if (this.parentsPath.includes('sites_group')) {
          this.siteGroupIdParent = data.site.id_sites_group;
        }

        // ajout des propriétés spécifiques au type de site
        // dans l'objet MonitoringObject
        const types_site = data.site['types_site'];
        this.obj['template_specific'] = this._monitoringObjServiceMonitoring
          .configService()
          .addSpecificConfig(types_site);

        this.visits = data.visits.items;
        this.page = {
          page: data.visits.page - 1,
          count: data.visits.count,
          limit: data.visits.limit,
        };

        this.baseFilters = { id_base_site: this.site.id_base_site };

        // Configuration du datatable
        let dataTableData = {
          visits: {
            data: data.visits,
            objConfig: data.objObsVisit,
          },
        };
        this.setDataTableObjData(dataTableData, this._configService, this.moduleCode, ['visit']);

        if (this.checkEditParam) {
          // Si mode édition demandé via le paramètre d'URL "edit"
          this._formService.changeFormMapObj({
            frmGp: this.form,
            obj: this.obj,
          });

          this.bEdit = true;
          this._formService.changeCurrentEditMode(this.bEdit);
        }
        this.obj.bIsInitialized = true;
      });
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
    this.dataTableObjData.visit.rows = this.rows;
    this.dataTableObjData.visit.page.count = visits.count;
    this.dataTableObjData.visit.page.limit = visits.limit;
    this.dataTableObjData.visit.page.page = visits.page - 1;
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
      this.siteService.getSiteModules(this.site.id_base_site, this.moduleCode).subscribe(
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
    const parentsPath = this.parentsPath;
    parentsPath.push('site');
    this.router.navigate(
      [
        `monitorings/object/${$event.module.module_code}/visit/${$event.id_base_visit}`,
        { edit: true },
      ],
      {
        queryParams: { id_base_site: this.site.id_base_site, parents_path: parentsPath },
      }
    );
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

  onbEditChange(event) {
    if (this.bEdit == true && event == false) {
      // Passage du mode édition au mode consultation : on suppose que des modifications de géométries
      //  ont pu être faites
      // Récupération et affichage de la géométrie du site
      this.geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
        id_base_site: this.site.id_base_site,
      });
    }
    this.bEdit = event;
    if (this.bEdit) {
      this._formService.changeFormMapObj({
        frmGp: this.form,
        obj: this.obj,
      });
    }
    this._formService.changeCurrentEditMode(this.bEdit);
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
    this._formService.changeCurrentEditMode(false);
    this._formService.changeFormMapObj({
      frmGp: null,
      obj: {},
    });
  }
}
