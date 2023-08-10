import { Component, OnInit, Input } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ReplaySubject, forkJoin, of } from 'rxjs';
import { tap, map, mergeMap, takeUntil } from 'rxjs/operators';
import * as L from 'leaflet';
import { IDataTableObj, ISite, ISiteField, ISitesGroup } from '../../interfaces/geom';
import { IPage, IPaginated } from '../../interfaces/page';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { setPopup } from '../../functions/popup';
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
  siteGroupLayer: L.FeatureGroup;
  @Input() bEdit: boolean;
  objForm: { static: FormGroup };
  objectType: IobjObs<ISite>;
  objParent: any;
  breadCrumbElemnt: IBreadCrumb = { label: 'Groupe de site', description: '' };
  breadCrumbElementBase: IBreadCrumb = breadCrumbElementBase;
  breadCrumbList: IBreadCrumb[] = [];
  rows_sites_table: ISiteField[];

  modules: SelectObject[];
  modulSelected;
  siteSelectedId: number;
  rows;
  dataTableObj: IDataTableObj;
  dataTableArray: {}[] = [];

  private destroyed$: ReplaySubject<boolean> = new ReplaySubject(1);

  constructor(
    public _sitesGroupService: SitesGroupService,
    private _siteService: SitesService,
    private _objService: ObjectService,
    private router: Router,
    private _Activatedroute: ActivatedRoute,
    private _geojsonService: GeoJSONService,
    private _configJsonService: ConfigJsonService,
    private _formBuilder: FormBuilder,
    private _configService: ConfigService
  ) {
    super();
    this.getAllItemsCallback = this.getSitesFromSiteGroupId;
  }

  ngOnInit() {
    this._geojsonService.removeFeatureGroup(this._geojsonService.sitesFeatureGroup);
    this.objForm = { static: this._formBuilder.group({}) };
    // this._sitesGroupService.init()
    this._objService.changeObjectTypeParent(this._sitesGroupService.objectObs);
    this._objService.changeObjectType(this._siteService.objectObs);
    this.initSite();
  }

  initSite() {
    this._Activatedroute.params
      .pipe(
        map((params) => params['id'] as number),
        tap((id: number) => {
          this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
            id_sites_group: id,
          });
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
        // this.siteGroupLayer = this._geojsonService.setMapData(
        //   data.sitesGroup.geometry,
        //   () => {}
        // );
        this.rows_sites_table = this._siteService.format_label_types_site(this.sites);
        this.baseFilters = { id_sites_group: this.sitesGroup.id_sites_group };
        this.colsname = objectObs.objObsSite.dataTable.colNameObj;
        this.objParent = objectObs.objObsSiteGp;

        data.sites['objConfig'] = objectObs.objObsSite;
        data.sitesGroup['objConfig'] = objectObs.objObsSiteGp;
        this.updateBreadCrumb(data.sitesGroup);
        this.setDataTableObj(data);
      });
  }
  ngOnDestroy() {
    this._geojsonService.removeFeatureGroup(this._geojsonService.sitesFeatureGroup);
    this.destroyed$.next(true);
    this.destroyed$.complete();
  }

  onEachFeatureSite() {
    const baseUrl = this.router.url + '/site';
    return (feature, layer) => {
      const popup = setPopup(
        baseUrl,
        feature.properties.id_base_site,
        'Site :' + feature.properties.base_site_name
      );
      layer.bindPopup(popup);
    };
  }

  getSitesFromSiteGroupId(page, params) {
    this._sitesGroupService
      .getSitesChild(page, LIMIT, params)
      .subscribe((data: IPaginated<ISite>) => {
        this.rows = this._siteService.format_label_types_site(data.items);
        this.dataTableObj.site.rows = this.rows;
        this.dataTableObj.site.page.count = data.count;
        this.dataTableObj.site.page.limit = data.limit;
        this.dataTableObj.site.page.page = data.page - 1;
      });
  }

  seeDetails($event) {
    this._objService.changeSelectedParentObj($event);
    this._objService.changeObjectTypeParent(this._siteService.objectObs);
    this.router.navigate([`site/${$event.id_base_site}`], {
      relativeTo: this._Activatedroute,
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
      objTemp[objType].rows = this._siteService.format_label_types_site(data[dataType].items);

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
