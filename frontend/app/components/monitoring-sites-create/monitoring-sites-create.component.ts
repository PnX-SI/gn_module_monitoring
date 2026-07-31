import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { ISite } from '../../interfaces/geom';
import { FormService } from '../../services/form.service';
import { SitesService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { GeoJSONService } from '../../services/geojson.service';
import { ConfigServiceG } from '../../services/config-g.service';

@Component({
  selector: 'monitoring-sites-create',
  templateUrl: './monitoring-sites-create.component.html',
  styleUrls: ['./monitoring-sites-create.component.css'],
})
export class MonitoringSitesCreateComponent implements OnInit {
  currentUser: User;

  public site: ISite | null;

  public moduleConfig: any;
  public form: FormGroup;
  public moduleCode: string;

  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public siteService: SitesService,
    public geojsonService: GeoJSONService,
    private _configServiceG: ConfigServiceG,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.moduleCode = this._route.snapshot.data.createSite.moduleCode;

    this.currentUser = this._auth.getCurrentUser();
    this.moduleConfig = this._configServiceG.config();
    this.form = this._formBuilder.group({});

    // Création d'un nouveau site
    this.site = null;

    // breadcrumb
    const queryParams = this._route.snapshot.queryParams;
    this._objService.loadBreadCrumb(this.moduleCode, 'site', null, queryParams);

    // Passage en mode édition
    this._formService.changeCurrentEditMode(true);
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
    this._formService.changeCurrentEditMode(false);
  }
}
