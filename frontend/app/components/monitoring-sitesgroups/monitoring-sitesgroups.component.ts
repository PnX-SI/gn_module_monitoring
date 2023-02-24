import { Component, OnInit, Input } from "@angular/core";
import { SitesGroupService } from "../../services/api-geom.service";
import { columnNameSiteGroup } from "../../class/monitoring-sites-group";
import { IPaginated, IPage } from "../../interfaces/page";
import { Router, ActivatedRoute } from "@angular/router";
import { columnNameSite } from "../../class/monitoring-site";
import { ISite, ISitesGroup } from "../../interfaces/geom";
import { GeoJSONService } from "../../services/geojson.service";
import { MonitoringGeomComponent } from "../../class/monitoring-geom-component";
import { setPopup } from "../../functions/popup";
import { ObjectService } from "../../services/object.service";
import { FormGroup, FormBuilder } from "@angular/forms";

const LIMIT = 10;

@Component({
  selector: "monitoring-sitesgroups",
  templateUrl: "./monitoring-sitesgroups.component.html",
  styleUrls: ["./monitoring-sitesgroups.component.css"],
})
export class MonitoringSitesGroupsComponent
  extends MonitoringGeomComponent
  implements OnInit
{
  @Input() page: IPage;
  @Input() sitesGroups: ISitesGroup[];
  @Input() sitesChild: ISite[];
  @Input() columnNameSiteGroup: typeof columnNameSiteGroup =
    columnNameSiteGroup;
  @Input() columnNameSite: typeof columnNameSite = columnNameSite;
  @Input() sitesGroupsSelected: ISitesGroup;

  // @Input() rows;
  @Input() colsname;
  @Input() obj;
  objectType: string;
  objForm: FormGroup;
  objInitForm: Object = {};
  // siteGroupEmpty={
  //   "comments" :'',
  //   sites_group_code: string;
  //   sites_group_description: string;
  //   sites_group_name: string;
  //   uuid_sites_group: string; //FIXME: see if OK
  // }

  constructor(
    private _sites_group_service: SitesGroupService,
    public geojsonService: GeoJSONService,
    private router: Router,
    private _objService: ObjectService,
    private _formBuilder: FormBuilder,
    private _Activatedroute: ActivatedRoute // private _routingService: RoutingService
  ) {
    super();
    this.getAllItemsCallback = this.getSitesGroups;
  }

  ngOnInit() {
    this.initSiteGroup();
  }

  initSiteGroup() {
    this._objService.changeObjectTypeParent(
      this._sites_group_service.editObjectType()
    );
    this._objService.changeObjectType(
      this._sites_group_service.addObjectType()
    );
    this.getSitesGroups(1);
    this.geojsonService.getSitesGroupsGeometries(
      this.onEachFeatureSiteGroups()
    );
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(
      this.geojsonService.sitesGroupFeatureGroup
    );
  }

  onEachFeatureSiteGroups(): Function {
    const baseUrl = this.router.url;
    return (feature, layer) => {
      const popup = setPopup(
        baseUrl,
        feature.properties.id_sites_group,
        "Groupe de site :" + feature.properties.sites_group_name
      );
      layer.bindPopup(popup);
    };
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
        this.colsname = this.columnNameSiteGroup;
        // IF prefered observable compare to ngOnChanges uncomment this:
        // this._dataTableService.changeColsTable(this.colsname,this.sitesGroups[0])
      });
  }

  seeDetails($event) {
    // TODO: routerLink
    this._objService.changeObjectTypeParent(
      this._sites_group_service.editObjectType()
    );
    this.router.navigate([$event.id_sites_group], {
      relativeTo: this._Activatedroute,
    });
  }

  addSiteGp($event) {
    this.router.navigate(["/create"], {
      relativeTo: this._Activatedroute,
    });
  }
  onSelect($event) {
    this.geojsonService.selectSitesGroupLayer($event);
  }
  onObjChanged($event) {}
}
