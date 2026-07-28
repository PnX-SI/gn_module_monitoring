import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { ActivatedRoute } from '@angular/router';
import { FormService } from '../../services/form.service';
import { MarkingsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { IMarking } from '../../interfaces/marking';

@Component({
  selector: 'monitoring-markings-create',
  templateUrl: './monitoring-markings-create.component.html',
  styleUrls: ['./monitoring-markings-create.component.css'],
})
export class MonitoringMarkingsCreateComponent implements OnInit, OnDestroy {
  currentUser: User;

  public marking: IMarking;

  public moduleConfig;
  public moduleCode;
  public form: FormGroup;

  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public _markingsService: MarkingsService,
    private _configServiceG: ConfigServiceG,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {
    // Initialisation des variables
    this.moduleConfig = this._configServiceG.config();
    this.moduleCode = this._configServiceG.moduleCode();
    this.form = this._formBuilder.group({});
    this.currentUser = this._auth.getCurrentUser();
    this._markingsService.initConfig();
    this.marking = {} as IMarking;

    // breadcrumb
    const queryParams = this._route.snapshot.queryParams;
    this.marking.id_individual = JSON.parse(queryParams?.id_individual);
    this._objService.loadBreadCrumb(this.moduleCode, 'marking', null, queryParams);

    // Passage en mode édition
    this._formService.changeCurrentEditMode(true);
  }

  ngOnDestroy() {
    this._formService.changeCurrentEditMode(false);
  }
}
