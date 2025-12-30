import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { ActivatedRoute } from '@angular/router';
import { ISitesGroup } from '../../interfaces/geom';
import { FormService } from '../../services/form.service';
import { SitesGroupService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { GeoJSONService } from '../../services/geojson.service';
import { ConfigServiceG } from '../../services/config-g.service';

@Component({
  selector: 'monitoring-sitesgroups-create',
  templateUrl: './monitoring-sitesgroups-create.component.html',
  styleUrls: ['./monitoring-sitesgroups-create.component.css'],
})
export class MonitoringSitesGroupsCreateComponent implements OnInit {
  currentUser: User;

  public sitesGroup: ISitesGroup;

  public moduleConfig;
  public form: FormGroup;

  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public _sitesGroupService: SitesGroupService,
    public geojsonService: GeoJSONService,
    private _configServiceG: ConfigServiceG,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {
    // Initialisation des variables
    this.moduleConfig = this._configServiceG.config();
    this.form = this._formBuilder.group({});
    this.currentUser = this._auth.getCurrentUser();
    // Création d'un nouvel objet site group
    this.sitesGroup = {} as ISitesGroup;

    // breadcrumb
    const queryParams = this._route.snapshot.queryParams;
    const moduleCode = this._configServiceG.moduleCode();
    this._objService.loadBreadCrumb(moduleCode, 'site', null, queryParams);


    // const elements = document.getElementsByClassName('monitoring-map-container');
    // if (elements.length >= 1) {
    //   elements[0].remove();
    // }

    // Passage en mode édition
    this._formService.changeCurrentEditMode(true);
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
    this._formService.changeCurrentEditMode(false);
  }
}
