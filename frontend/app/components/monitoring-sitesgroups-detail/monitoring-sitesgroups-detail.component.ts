import { Component, OnInit, Input, EventEmitter } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ReplaySubject, forkJoin, of } from 'rxjs';
import { mergeMap, takeUntil } from 'rxjs/operators';
import { ISite, ISitesGroup } from '../../interfaces/geom';
import { IPage, IPaginated } from '../../interfaces/page';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { GeoJSONService } from '../../services/geojson.service';
import { FormBuilder } from '@angular/forms';
import { SitesService, SitesGroupService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { SelectObject } from '../../interfaces/object';
import { Module } from '../../interfaces/module';
import { FormService } from '../../services/form.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { PermissionService } from '../../services/permission.service';
import { resolveObjectProperties } from '../../utils/utils';
import { CacheService } from '../../services/cache.service';

@Component({
  selector: 'monitoring-sitesgroups-detail',
  templateUrl: './monitoring-sitesgroups-detail.component.html',
  styleUrls: ['./monitoring-sitesgroups-detail.component.css'],
})
export class MonitoringSitesgroupsDetailComponent
  extends MonitoringGeomComponent
  implements OnInit
{
  sitesGroup: ISitesGroup;
  page: IPage;

  public objectType: string = 'site';

  modules: SelectObject[];
  siteSelectedId: number;
  rows;
  siteResolvedProperties;

  sitesGroupResolved;
  private destroyed$: ReplaySubject<boolean> = new ReplaySubject(1);

  bDeleteModalEmitter = new EventEmitter<boolean>();

  constructor(
    protected _Activatedroute: ActivatedRoute,
    protected _formBuilder: FormBuilder,
    protected _auth: AuthService,
    public _sitesGroupService: SitesGroupService,
    private _siteService: SitesService,
    private _objService: ObjectService,
    private router: Router,
    private _geojsonService: GeoJSONService,
    public _formService: FormService,
    public _permissionService: PermissionService,
    public _popup: Popup,
    private _cacheService: CacheService
  ) {
    super(_permissionService, _popup, _formService, _Activatedroute, _formBuilder, _auth);
    this.getAllItemsCallback = this.getSitesFromSiteGroupId;
  }

  ngOnInit() {
    super.ngOnInit();
    this.baseFilters = { id_sites_group: this.dataId };
    // breadcrumb
    this._objService.loadBreadCrumb(this.moduleCode, 'sites_group', this.dataId, this.queryParams);
    this.initSite();
  }

  initSite() {
    const fieldsConfig = this._configServiceG.config()['site']['fields'];
    const siteGroupdata$ = this._sitesGroupService.getById(this.dataId);

    siteGroupdata$
      .pipe(
        mergeMap((sitesGroupData) => {
          this.sitesGroup = sitesGroupData;
          const siteGroupDataResolved$ = resolveObjectProperties(
            this.sitesGroup,
            fieldsConfig,
            this._configServiceG,
            this._cacheService
          );
          const sitedata$ = this._sitesGroupService.getSitesChildResolved(
            1,
            this.limit,
            this.baseFilters,
            fieldsConfig
          );
          return forkJoin({
            sitesGroupResolved: siteGroupDataResolved$,
            sites: sitedata$,
          });
        })
      )
      .subscribe((data) => {
        this.sitesGroupResolved = data.sitesGroupResolved;
        const sites = data.sites;
        this.page = {
          count: sites.count,
          page: sites.page,
          limit: sites.limit,
        };

        this.setDataTableObjData(
          {
            sites: {
              data: sites,
              objType: 'site',
              childType: 'visit',
            },
          },
          this.moduleCode,
          ['site', 'individual']
        );

        this.rows = this.dataTableObjData.site.rows;
        this.getSitesFromSiteGroupId(this.page.page, {});
      });
  }

  ngOnDestroy() {
    super.ngOnDestroy();
    this._geojsonService.removeAllFeatureGroup();
    this.destroyed$.next(true);
    this.destroyed$.complete();
    this._formService.changeCurrentEditMode(false);
  }

  onbEditChange(event: boolean) {
    if (this.bEdit == true && event == false) {
      // Passage du mode édition au mode consultation : on suppose que des modifications de géométries
      //  ont pu être faites
      // Récupération et affichage de la géométrie du site
      this.initSite();
      const sitesParams = { ...{}, ...this.baseFilters };
      this._geojsonService.getSitesGroupsGeometriesWithSites(
        this.onEachFeatureGroupSite(),
        this.onEachFeatureSite(),
        this.baseFilters,
        sitesParams
      );
    }
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
    const fieldsConfig = this._configServiceG.config()['site']['fields'];
    this._sitesGroupService
      .getSitesChildResolved(1, this.limit, sitesParams, fieldsConfig)
      .subscribe((data: IPaginated<ISite>) => {
        const siteList = data.items;
        this.rows = siteList;
        this.siteResolvedProperties = siteList;
        this.dataTableObjData.site.rows = this.rows;
        this.dataTableObjData.site.page.count = data.count;
        this.dataTableObjData.site.page.limit = data.limit;
        this.dataTableObjData.site.page.page = data.page - 1;
      });
    // Données carto
    this._geojsonService.getSitesGroupsGeometriesWithSites(
      this.onEachFeatureGroupSite(),
      this.onEachFeatureSite(),
      this.baseFilters,
      sitesParams
    );
  }

  seeDetails($event) {
    this.router.navigate([`/monitorings/object/${this.moduleCode}/site/${$event.id_base_site}`], {
      queryParams: { parents_path: ['module', 'sites_group'] },
    });
  }

  editChild($event) {
    this.router.navigate([`/monitorings/object/${this.moduleCode}/site/${$event.id_base_site}`], {
      queryParams: { parents_path: ['module', 'sites_group'], edit: true },
    });
  }

  navigateToAddObj($event) {
    const type = $event;
    const queryParams = {
      parents_path: ['module', 'sites_group'],
    };

    queryParams['id_sites_group'] = this.dataId;
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
    this._siteService
      .getSiteModules(this.siteSelectedId, this.moduleCode)
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
    const moduleCode = event.id;
    const keys = Object.keys(this._configServiceG.config());
    const parents_path = ['sites_group', 'site'].filter((item) => keys.includes(item));
    this.router.navigate([`monitorings/object/${moduleCode}/visit/create`], {
      queryParams: { id_base_site: this.siteSelectedId, parents_path: parents_path },
    });
  }
}
