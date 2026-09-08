import { Component, Input, OnInit, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { ModuleService } from '@geonature/services/module.service';

import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { ISite } from '../../interfaces/geom';
import { IPage, IPaginated } from '../../interfaces/page';
import { IVisit } from '../../interfaces/visit';
import { SitesService, VisitsService } from '../../services/api-geom.service';
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
import { resolveObjectProperties } from '../../utils/utils';

import { CacheService } from '../../services/cache.service';

@Component({
  selector: 'monitoring-sites-detail',
  templateUrl: './monitoring-sites-detail.component.html',
  styleUrls: ['./monitoring-sites-detail.component.css'],
})
export class MonitoringSitesDetailComponent extends MonitoringGeomComponent implements OnInit {
  @Input() visits: IPaginated<IVisit>;
  @Input() page: IPage;
  // form: FormGroup;
  modules: SelectObject[];

  public objectType: string = 'site';

  site: ISite;

  siteGroupIdParent: number;
  rows;

  bDeleteModalEmitter = new EventEmitter<boolean>();

  currentUser: User;

  constructor(
    protected _Activatedroute: ActivatedRoute,
    protected _formBuilder: FormBuilder,
    protected _auth: AuthService,
    private _visits_service: VisitsService,
    private _objService: ObjectService,
    public geojsonService: GeoJSONService,
    private router: Router,
    public _formService: FormService,
    private _configService: ConfigService,
    protected _moduleService: ModuleService,
    public _siteService: SitesService,
    private _objServiceMonitoring: DataMonitoringObjectService,
    public _permissionService: PermissionService,
    public _popup: Popup,
    private _cacheService: CacheService
  ) {
    super(_permissionService, _popup, _formService, _Activatedroute, _formBuilder, _auth);
    this.getAllItemsCallback = this.getVisits;
    this.objectType = 'site';
  }

  ngOnInit() {
    super.ngOnInit();
    // breadcrumb
    this._objService.loadBreadCrumb(
      this.moduleCode,
      this.objectType,
      this.dataId,
      this.queryParams
    );
    // initialisation des données
    this.initSiteVisit();
  }

  initSiteVisit() {
    this._permissionService.setPermissionMonitorings(this.moduleCode);
    forkJoin({
      site: this._siteService.getById(this.dataId, this.moduleCode),
      visits: this._visits_service.getResolved(1, this.limit, {
        id_base_site: this.dataId,
      }),
    }).subscribe((data) => {
      this.objectData = data.site;
      const fieldsConfig = this._configServiceG.config()[this.objectType]['fields'];
      // Resolve site data
      resolveObjectProperties(
        this.objectData,
        fieldsConfig,
        this._configServiceG,
        this._cacheService
      ).subscribe((data) => {
        this.objectDataResolved = data;
      });

      if (this.parentPath.includes('sites_group')) {
        this.siteGroupIdParent = this.objectData.id_sites_group;
      }
      if (this.siteGroupIdParent) {
        // Quand il y a un group de site défini affichage du groupes de sites
        //  et autre sites associés pour avoir des repères
        this.geojsonService.getSitesGroupsGeometriesWithSites(
          this.onEachFeatureSite(),
          this.onEachFeatureSite(),
          { id_sites_group: this.siteGroupIdParent },
          { id_sites_group: this.siteGroupIdParent }
        );
      } else {
        // Récupération et affichage de la géométrie du site
        this.geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
          id_base_site: this.dataId,
        });
      }

      this.visits = data.visits || { items: [], page: 1, limit: this.limit, count: 0 };
      this.page = {
        page: this.visits.page - 1,
        count: this.visits.count,
        limit: this.visits.limit,
      };

      this.baseFilters = { id_base_site: this.objectData.id_base_site };

      // Configuration du datatable
      let dataTableData = {
        visits: {
          data: data.visits,
          objType: 'visit',
          childType: 'observation',
        },
      };
      this.setDataTableObjData(dataTableData, this.moduleCode, ['visit']);
    });
  }

  onEachFeatureSite() {
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(this.moduleCode, feature, {});
      layer.bindPopup(popup);
    };
  }

  getVisits(page: number, filters: JsonData) {
    const queryParams = { ...filters, ...{ id_base_site: this.objectData.id_base_site } };
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
    const parentPath = [...this.parentPath];
    if (!parentPath.includes('site')) {
      parentPath.push('site');
    }
    this.router.navigate(
      [`/monitorings/object/${$event.module.module_code}/visit/${$event.id_base_visit}`],
      {
        queryParams: { parents_path: parentPath },
      }
    );
  }

  getModules() {
    if (this.moduleCode === 'generic') {
      this._siteService.getSiteModules(this.objectData.id_base_site, this.moduleCode).subscribe(
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
    const keys = Object.keys(this._configServiceG.config());
    const parents_path = ['sites_group', 'site'].filter((item) => keys.includes(item));
    this.router.navigate([`monitorings/object/${moduleCode}/visit/create`], {
      queryParams: { id_base_site: this.objectData.id_base_site, parents_path: parents_path },
    });
  }

  navigateToAddObj($event) {
    const type = $event;

    const parentPath = [...this.parentPath];
    if (!parentPath.includes('site')) {
      parentPath.push('site');
    }
    const queryParams = {
      parents_path: parentPath,
      id_base_site: this.objectData.id_base_site,
    };
    this.router.navigate([`/monitorings/object/${this.moduleCode}/`, type, 'create'], {
      queryParams: queryParams,
    });
  }

  editChild($event) {
    const parentPath = [...this.parentPath];
    if (!parentPath.includes('site')) {
      parentPath.push('site');
    }
    this.router.navigate(
      [`monitorings/object/${$event.module.module_code}/visit/${$event.id_base_visit}`],
      {
        queryParams: {
          id_base_site: this.objectData.id_base_site,
          parents_path: parentPath,
          edit: true,
        },
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
        id_base_site: this.objectData.id_base_site,
      });
    }
    this.bEdit = event;
  }

  ngOnDestroy() {
    super.ngOnDestroy();
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
    this._formService.changeCurrentEditMode(false);
  }
}
