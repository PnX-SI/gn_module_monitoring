import { Component, OnInit, Input } from '@angular/core';
import { SitesGroupService, SitesService } from '../../services/api-geom.service';
import { IPaginated, IPage } from '../../interfaces/page';
import { Router, ActivatedRoute } from '@angular/router';
import { IDataTableObj, ISite, ISitesGroup } from '../../interfaces/geom';
import { GeoJSONService } from '../../services/geojson.service';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { setPopup } from '../../functions/popup';
import { ObjectService } from '../../services/object.service';
import { FormGroup, FormBuilder } from '@angular/forms';
import { IobjObs } from '../../interfaces/objObs';
import { ConfigJsonService } from '../../services/config-json.service';
import { IBreadCrumb } from '../../interfaces/object';
import { breadCrumbElementBase } from '../breadcrumbs/breadcrumbs.component';
import { FormService } from '../../services/form.service';
import { JsonData } from '../../types/jsondata';

const LIMIT = 10;

@Component({
  selector: 'monitoring-sitesgroups',
  templateUrl: './monitoring-sitesgroups.component.html',
  styleUrls: ['./monitoring-sitesgroups.component.css'],
})
export class MonitoringSitesGroupsComponent extends MonitoringGeomComponent implements OnInit {
  @Input() page: IPage;
  @Input() sitesGroups: ISitesGroup[];
  @Input() sitesChild: ISite[];
  @Input() sitesGroupsSelected: ISitesGroup;

  @Input() obj;
  colsname: {};
  objectType: IobjObs<ISitesGroup>;
  objForm: FormGroup;
  objInitForm: Object = {};
  breadCrumbElementBase: IBreadCrumb = breadCrumbElementBase;

  rows;
  dataTableObj: IDataTableObj;
  dataTableArray: {}[] = [];

  // siteGroupEmpty={
  //   "comments" :'',
  //   sites_group_code: string;
  //   sites_group_description: string;
  //   sites_group_name: string;
  //   uuid_sites_group: string; //FIXME: see if OK
  // }

  constructor(
    private _sites_group_service: SitesGroupService,
    private _sitesService: SitesService,
    public geojsonService: GeoJSONService,
    private router: Router,
    private _objService: ObjectService,
    private _formBuilder: FormBuilder,
    private _configJsonService: ConfigJsonService,
    private _Activatedroute: ActivatedRoute, // private _routingService: RoutingService
    private _formService: FormService
  ) {
    super();
    this.getAllItemsCallback = this.getSitesOrSitesGroups; //[this.getSitesGroups, this.getSites];
  }

  ngOnInit() {
    this.initSiteGroup();
    this._objService.changeSelectedObj({}, true);
    // this._formService.changeFormMapObj({frmGp: this._formBuilder.group({}),bEdit:false, objForm: {}})
  }

  initSiteGroup() {
    this._objService.changeObjectTypeParent(this._sites_group_service.objectObs);
    this._objService.changeObjectType(this._sites_group_service.objectObs);

    this.updateBreadCrumb();
    this._Activatedroute.data.subscribe(({ data }) => {
      this.page = {
        count: data.sitesGroups.data.count,
        limit: data.sitesGroups.data.limit,
        page: data.sitesGroups.data.page - 1,
      };

      this.sitesGroups = data.sitesGroups.data.items;
      // this.columns = [data.sitesGroups.data.items, data.sites.data.items]
      this.colsname = data.sitesGroups.objConfig.dataTable.colNameObj;
      this.setDataTableObj(data);
    });
    this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups());
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
  }

  onEachFeatureSiteGroups(): Function {
    const baseUrl = this.router.url;
    return (feature, layer) => {
      const popup = setPopup(
        baseUrl,
        feature.properties.id_sites_group,
        'Groupe de site :' + feature.properties.sites_group_name
      );
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
  }

  getSites(page = 1, params = {}) {
    this._sitesService.get(page, LIMIT, params).subscribe((data: IPaginated<ISite>) => {
      this.colsname = this._sitesService.objectObs.dataTable.colNameObj;
      this.rows = this._sitesService.format_label_types_site(data.items);
      this.dataTableObj.site.rows = this.rows;
      this.dataTableObj.site.page.count = data.count;
      this.dataTableObj.site.page.limit = data.limit;
      this.dataTableObj.site.page.page = data.page - 1;
    });
  }

  getGeometriesSite() {
    this.geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite());
  }

  onEachFeatureSite() {
    const baseUrl = this.router.url;
    return (feature, layer) => {
      const popup = setPopup(
        baseUrl,
        feature.properties.id_base_site,
        'Site :' + feature.properties.base_site_name
      );
      layer.bindPopup(popup);
    };
  }
  seeDetails($event) {
    // TODO: routerLink
    this._objService.changeObjectTypeParent(this._sites_group_service.objectObs);
    this.router.navigate([$event.id_sites_group], {
      relativeTo: this._Activatedroute,
    });
  }

  addSiteGp($event) {
    this.router.navigate(['/create'], {
      relativeTo: this._Activatedroute,
    });
  }

  updateBreadCrumb() {
    this._objService.changeBreadCrumb([this.breadCrumbElementBase], true);
  }

  onSelect($event) {
    this.geojsonService.selectSitesGroupLayer($event);
  }

  loadGeoJson($event) {
    if ($event == 'site') {
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
      this.getGeometriesSite();
    } else {
      this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
      this.geojsonService.getSitesGroupsGeometries(this.onEachFeatureSiteGroups());
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
        objTemp[objType].rows = this._sitesService.format_label_types_site(
          data[dataType].data.items
        );
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
}
