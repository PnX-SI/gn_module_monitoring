import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { ActivatedRoute } from '@angular/router';
import { FormService } from '../../services/form.service';
import { ObservationDetailsService, SitesGroupService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { GeoJSONService } from '../../services/geojson.service';
import { Popup } from '../../utils/popup';
import { IObservationDetail } from '../../interfaces/observationdetail';
import { JsonData } from '../../types/jsondata';

@Component({
  selector: 'monitoring-observationsdetail-create',
  templateUrl: './monitoring-observationsdetail-create.component.html',
  styleUrls: ['./monitoring-observationsdetail-create.component.css'],
})
export class MonitoringObservationsDetailCreateComponent implements OnInit {
  currentUser: User;

  public observation_detail: IObservationDetail;

  public moduleConfig;
  public moduleCode;
  public form: FormGroup;
  public fetchedParents: JsonData | null;

  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public _sitesGroupService: SitesGroupService,
    public _observationsDetailService: ObservationDetailsService,
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
    this.fetchedParents = this._route.snapshot.data.resolvedData.parents;

    // breadcrumb
    const queryParams = this._route.snapshot.queryParams;
    const moduleCode = this._configServiceG.moduleCode();
    this.observation_detail.id_observation = JSON.parse(queryParams?.id_observation);
    this._objService.loadBreadCrumb(moduleCode, 'observation_detail', null, queryParams);
    // Passage en mode édition
    this._formService.changeCurrentEditMode(true);

    const id_base_site = this.fetchedParents?.site.id_base_site;
    // Récupération et affichage de la géométrie du site
    this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
      id_base_site: id_base_site,
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
