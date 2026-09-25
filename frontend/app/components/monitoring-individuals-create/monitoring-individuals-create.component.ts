import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { ActivatedRoute } from '@angular/router';
import { FormService } from '../../services/form.service';
import { IndividualsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { IIndividual } from '../../interfaces/individual';

@Component({
  selector: 'monitoring-individuals-create',
  templateUrl: './monitoring-individuals-create.component.html',
  styleUrls: ['./monitoring-individuals-create.component.css'],
})
export class MonitoringIndividualsCreateComponent implements OnInit, OnDestroy {
  currentUser: User;

  public individual: IIndividual;

  public moduleConfig;
  public moduleCode;
  public form: FormGroup;

  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public _individualsService: IndividualsService,
    private _configServiceG: ConfigServiceG,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {
    // Initialisation des variables
    this.moduleConfig = this._configServiceG.config();
    this.moduleCode = this._configServiceG.moduleCode();
    this.form = this._formBuilder.group({});
    this.currentUser = this._auth.getCurrentUser();
    this._individualsService.initConfig();
    this.individual = {} as IIndividual;

    // breadcrumb
    const queryParams = this._route.snapshot.queryParams;
    this._objService.loadBreadCrumb(this.moduleCode, 'individual', null, queryParams);

    // Passage en mode édition
    this._formService.changeCurrentEditMode(true);
  }

  ngOnDestroy() {
    this._formService.changeCurrentEditMode(false);
  }
}
