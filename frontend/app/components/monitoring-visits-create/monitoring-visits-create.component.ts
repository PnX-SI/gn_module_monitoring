import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { ActivatedRoute } from '@angular/router';
import { FormService } from '../../services/form.service';
import { SitesGroupService, VisitsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { IVisit } from '../../interfaces/visit';
import { GeoJSONService } from '../../services/geojson.service';
import { Popup } from '../../utils/popup';

@Component({
  selector: 'monitoring-visits-create',
  templateUrl: './monitoring-visits-create.component.html',
  styleUrls: ['./monitoring-visits-create.component.css'],
})
export class MonitoringVisitsCreateComponent implements OnInit {
  currentUser: User;

  public visit: IVisit;

  public moduleConfig;
  public moduleCode;
  public form: FormGroup;

  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public _sitesGroupService: SitesGroupService,
    public _visitsService: VisitsService,
    private _configServiceG: ConfigServiceG,
    private _route: ActivatedRoute,
    private _geojsonService: GeoJSONService,
    private _popup: Popup
  ) {}

  ngOnInit() {
    // Initialisation des variables
    this.moduleConfig = this._configServiceG.config();
    this.moduleCode = this._configServiceG.moduleCode();
    this.form = this._formBuilder.group({});
    this.currentUser = this._auth.getCurrentUser();
    this._visitsService.initConfig();
    this.visit = {} as IVisit;
    // breadcrumb
    const queryParams = this._route.snapshot.queryParams;
    const moduleCode = this._configServiceG.moduleCode();
    this.visit.id_base_site = JSON.parse(queryParams?.id_base_site);
    this._objService.loadBreadCrumb(moduleCode, 'visit', null, queryParams);
    // Passage en mode édition
    this._formService.changeCurrentEditMode(true);

    // Récupération et affichage de la géométrie du site
    this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
      id_base_site: this.visit.id_base_site,
    });
  }

  onEachFeatureSite() {
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(this.moduleCode, feature, {});
      layer.bindPopup(popup);
    };
  }
  ngOnDestroy() {
    this._geojsonService.removeFeatureGroup(this._geojsonService.sitesFeatureGroup);
    this._formService.changeCurrentEditMode(false);
  }
}
