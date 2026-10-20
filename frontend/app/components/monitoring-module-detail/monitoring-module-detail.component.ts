import { Location } from '@angular/common';
import { Component, EventEmitter, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';

import { Module } from '../../interfaces/module';
import { SelectObject } from '../../interfaces/object';

import { IPage, IPaginated } from '../../interfaces/page';

import {
  IndividualsService,
  ModuleService,
  SitesGroupService,
  SitesService,
} from '../../services/api-geom.service';
import { FormService } from '../../services/form.service';
import { GeoJSONService } from '../../services/geojson.service';

import { ObjectService } from '../../services/object.service';
import { TPermission } from '../../types/permission';
import { Popup } from '../../utils/popup';

const LIMIT = 10;

import { ReplaySubject } from 'rxjs';
import { mergeMap, takeUntil } from 'rxjs/operators';
import { PermissionService } from '../../services/permission.service';
import { ObjectType } from '../../enum/objecttype';
import { DataUtilsService } from '../../services/data-utils.service';

@Component({
  selector: 'monitoring-module-detail',
  templateUrl: './monitoring-module-detail.component.html',
  styleUrls: ['./monitoring-module-detail.component.css'],
})
export class MonitoringModuleDetailComponent extends MonitoringGeomComponent implements OnInit {
  obj;
  resolvedObj;
  public bDeleteModalEmitter: EventEmitter<boolean> = new EventEmitter<boolean>();
  public page: IPage;

  public objectType: string = 'module';
  public allowedObjectTypes: string[] = ['site', 'sites_group', 'individual'];

  objInitForm: Object = {};
  rows;
  dataTableConfig: {}[] = [];
  activetabIndex: number;
  currentRoute: string;

  modules: SelectObject[];

  private destroyed$: ReplaySubject<boolean> = new ReplaySubject(1);

  siteResolvedProperties;

  currentPermission: TPermission;

  // Module configuré : liste d'observateurs, jeu(x) de données, liste de taxons
  // et affichage des taxons renseignés
  isConfigured: boolean = true;

  // TODO: move to a common file
  private childTypes: { [index: string]: string } = {
    site: 'visit',
    sites_group: 'site',
    individual: 'marking',
  };

  constructor(
    protected _Activatedroute: ActivatedRoute,
    protected _formBuilder: FormBuilder,
    protected _auth: AuthService,
    private _sites_group_service: SitesGroupService,
    private _sitesService: SitesService,
    private _individualService: IndividualsService,
    public _geojsonService: GeoJSONService,
    protected router: Router,
    private _objService: ObjectService,
    public _formService: FormService,
    private _location: Location,
    public _popup: Popup,
    public _permissionService: PermissionService,
    public _moduleService: ModuleService,
    private _dataUtilsService: DataUtilsService
  ) {
    super(_permissionService, _popup, _formService, _Activatedroute, _formBuilder, _auth, router);
    this.getAllItemsCallback = this.getData;
  }

  ngOnInit() {
    super.ngOnInit();
    this._geojsonService.removeFeatureGroup(this._geojsonService.sitesFeatureGroup);
    this.initData();
  }

  initData() {
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

      this.currentPermission = data.permission;
      this.currentRoute = data.route;
      this.isConfigured = this._configServiceG.config()?.configured !== false;

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

      // Pas de récupération des géométries si le module n'est pas configuré
      if (this.isConfigured) {
        if (data.route == ObjectType.site) {
          this.currentPermission.site.R > 0
            ? this.getGeometriesSite(this.dataTableConfig[this.activetabIndex]['defaultFilters'])
            : null;
        } else {
          this.currentPermission.sites_group.R > 0
            ? this._geojsonService.getSitesGroupsGeometries(
                this.onEachFeatureSiteGroups(),
                this.dataTableConfig[this.activetabIndex]['defaultFilters']
              )
            : null;
        }
      }

      if (this.moduleCode != 'generic') {
        // this._moduleService.getModulebyCode(this.moduleCode).subscribe((data) => {
        this._moduleService.getByModuleCode(this.moduleCode).subscribe((data) => {
          this.objectData = data;
          this._dataUtilsService
            .resolveObjectProperties(
              this.objectData,
              this._configServiceG.config()['module']['fields']
            )
            .subscribe((data) => {
              this.resolvedObj = data;
            });
        });
      }
    });
  }

  configureModule() {
    this._formService.changeCurrentEditMode(true);
  }

  ngOnDestroy() {
    super.ngOnDestroy();
    this._geojsonService.removeFeatureGroup(this._geojsonService.sitesGroupFeatureGroup);
    this._geojsonService.removeFeatureGroup(this._geojsonService.sitesFeatureGroup);
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
    this._geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups(), params);
  }

  getIndividuals(page = 1, params = {}) {
    this.updateDataTableContent(page, params, this._individualService);
  }

  getSites(page = 1, params = {}) {
    this.updateDataTableContent(page, params, this._sitesService);
    this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), params);
  }

  getGeometriesSite(params = {}) {
    this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), params);
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
    this.router.navigate(
      [`/monitorings/object/${this.moduleCode}/`, this.currentRoute, $event[$event.id]],
      {
        queryParams: queryParams,
      }
    );
  }

  navigateToAddChildren($event) {
    const row = $event;
    if (row) {
      row['id'] = row[row.pk];
      let queryParams = {};
      queryParams[row['pk']] = row['id'];
      const current_object = this.dataTableConfig[this.activetabIndex]['objectType'];
      queryParams['parents_path'] = ['module', current_object];
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
  onbEditChange(event: boolean) {
    if (this.bEdit == true && event == false) {
      // Passage du mode édition au mode consultation
      if (this.objectData.deleted !== true) {
        this.initData();
      }
    }
    this.bEdit = event;
  }

  onDelete(event) {
    this.currentRoute = event.objectType;
    const queryParams = { module_code: this.moduleCode };
    let delete$;
    if (event.objectType == ObjectType.sites_group) {
      delete$ = this._sites_group_service.delete(event.rowSelected.id_sites_group, queryParams);
    } else if (event.objectType == ObjectType.individual) {
      delete$ = this._individualService.delete(event.rowSelected.id_individual, queryParams);
    } else {
      delete$ = this._sitesService.delete(event.rowSelected.id_base_site, queryParams);
    }
    delete$.subscribe(() => {
      this.bDeleteModalEmitter.emit(false);
      this.refreshAfterDelete(event.objectType);
    });
  }

  /**
   * Rafraîchit le tableau (et la carte) de l'onglet courant sans recharger la route,
   * en conservant la page et les filtres en cours.
   * Si la ligne supprimée était la dernière de la page, revient à la page précédente.
   */
  refreshAfterDelete(objectType: ObjectType) {
    const page = this.dataTableObjData[objectType]?.page;
    let pageNumber = page ? page.page + 1 : 1;
    if (page && pageNumber > 1 && page.count - 1 <= page.page * page.limit) {
      pageNumber -= 1;
    }
    const tabConfig: any = this.dataTableConfig[this.getdataTableIndex(objectType)];
    const defaultFilters = tabConfig?.defaultFilters || {};
    this.getData(pageNumber, { ...defaultFilters, ...this.filters }, objectType);
  }

  onSelectedOnDataTable(data) {
    const typeObject = data[0];
    const id = data[1];
    if (typeObject == 'site') {
      this._geojsonService.selectSitesLayer(id, true);
    } else if (typeObject == 'sites_group') {
      this._geojsonService.selectSitesGroupLayer(id, true);
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
      this._geojsonService.removeFeatureGroup(this._geojsonService.sitesGroupFeatureGroup);
      this.currentPermission.site.R > 0 ? this.getGeometriesSite() : null;
    } else if ($event == 'individual') {
      this.currentRoute = 'individual';
      this._location.go(`/monitorings/object/${this.moduleCode}/individual`);
      this._geojsonService.removeFeatureGroup(this._geojsonService.sitesGroupFeatureGroup);
      this.currentPermission.site.R > 0 ? this.getGeometriesSite() : null;
    } else {
      this.currentRoute = 'sites_group';
      this._location.go(`/monitorings/object/${this.moduleCode}/sites_group`);
      this._geojsonService.removeFeatureGroup(this._geojsonService.sitesFeatureGroup);
      this.currentPermission.sites_group.R > 0
        ? this._geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups())
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
    this.router.navigate([`monitorings/object/${this.moduleCode}/visit/create`], {
      queryParams: { id_base_site: idSite, parents_path: parents_path },
    });
  }
}
