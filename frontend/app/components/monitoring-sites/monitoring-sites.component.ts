import { Component, OnInit, Input } from "@angular/core";
import { ActivatedRoute, Router } from "@angular/router";
import { forkJoin } from "rxjs";
import { tap, map, mergeMap } from "rxjs/operators";
import * as L from "leaflet";
import { ISite, ISitesGroup } from "../../interfaces/geom";
import { IPage, IPaginated } from "../../interfaces/page";
import { MonitoringGeomComponent } from "../../class/monitoring-geom-component";
import { setPopup } from "../../functions/popup";
import { GeoJSONService } from "../../services/geojson.service";
import { FormGroup, FormBuilder } from "@angular/forms";
import {
  SitesService,
  SitesGroupService,
} from "../../services/api-geom.service";
import { ObjectService } from "../../services/object.service";
import { IobjObs } from "../../interfaces/objObs";
import { IBreadCrumb } from "../../interfaces/object";
import { breadCrumbElementBase } from "../breadcrumbs/breadcrumbs.component";

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
  objForm: FormGroup;
  objectType: IobjObs<ISite>;
  objParent: any;
  breadCrumbElemnt: IBreadCrumb = { label: 'Groupe de site', description: '' };
  breadCrumbElementBase: IBreadCrumb = breadCrumbElementBase;
  breadCrumbList: IBreadCrumb[] = [];
  constructor(
    public _sitesGroupService: SitesGroupService,
    private _siteService: SitesService,
    private _objService: ObjectService,
    private router: Router,
    private _Activatedroute: ActivatedRoute,
    private _geojsonService: GeoJSONService,
    private _formBuilder: FormBuilder
  ) {
    super();
    this.getAllItemsCallback = this.getSitesFromSiteGroupId;
  }

  ngOnInit() {
    this.objForm = this._formBuilder.group({});
    // this._sitesGroupService.init()
    this._objService.changeObjectTypeParent(this._sitesGroupService.objectObs, true);
    this._objService.currentObjectTypeParent.subscribe((objParent) => {
      this.objParent = objParent;
    });
    this._objService.changeObjectType(this._siteService.objectObs, true);
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
        mergeMap((id: number) =>
          forkJoin({
            sitesGroup: this._sitesGroupService.getById(id),
            sites: this._sitesGroupService.getSitesChild(1, this.limit, {
              id_sites_group: id,
            }),
          })
        )
      )
      .subscribe((data) => {
        console.log(data);
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
        this.baseFilters = { id_sites_group: this.sitesGroup.id_sites_group };
        this.colsname = this._siteService.objectObs.dataTable.colNameObj;
        this._objService.changeSelectedParentObj(data.sitesGroup, true);
        this.updateBreadCrumb(data.sitesGroup);
      });
  }
  ngOnDestroy() {
    this._geojsonService.removeFeatureGroup(this._geojsonService.sitesFeatureGroup);
    this._geojsonService.removeFeatureGroup(this.siteGroupLayer);
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

  getSitesFromSiteGroupId(page, params) {
    this._sitesGroupService
      .getSitesChild(page, LIMIT, params)
      .subscribe((data: IPaginated<ISite>) => {
        this.sites = data.items;
        this.page = {
          count: data.count,
          limit: data.limit,
          page: data.page - 1,
        };
      });
  }

  seeDetails($event) {
    this._objService.changeObjectTypeParent(this._siteService.objectObs, true);
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
    this.initSite();
  }
}
