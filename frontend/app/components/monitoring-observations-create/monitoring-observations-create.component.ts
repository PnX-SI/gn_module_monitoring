import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { ActivatedRoute } from '@angular/router';
import { FormService } from '../../services/form.service';
import { ObservationsService, SitesGroupService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { IObservation } from '../../interfaces/observation';
import { GeoJSONService } from '../../services/geojson.service';
import { Popup } from '../../utils/popup';

@Component({
  selector: 'monitoring-observations-create',
  templateUrl: './monitoring-observations-create.component.html',
  styleUrls: ['./monitoring-observations-create.component.css'],
})
export class MonitoringObservationsCreateComponent implements OnInit {
  currentUser: User;

  public observation: IObservation;

  public moduleConfig;
  public moduleCode;
  public form: FormGroup;

  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public _sitesGroupService: SitesGroupService,
    public _observationsService: ObservationsService,
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
    this._observationsService.initConfig();
    this.observation = {} as IObservation;
    // breadcrumb
    const queryParams = this._route.snapshot.queryParams;
    const moduleCode = this._configServiceG.moduleCode();
    this.observation.id_base_visit = JSON.parse(queryParams?.id_base_visit);
    this.observation.id_base_site = JSON.parse(queryParams?.id_base_site);
    this._objService.loadBreadCrumb(moduleCode, 'observation', null, queryParams);
    // Passage en mode édition
    this._formService.changeCurrentEditMode(true);

    // Récupération et affichage de la géométrie du site
    this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
      id_base_site: this.observation.id_base_site,
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
