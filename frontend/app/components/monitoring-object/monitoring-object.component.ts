import { Observable } from "rxjs/Observable";
import "rxjs/add/observable/forkJoin";

import { MonitoringObject } from '../../class/monitoring-object';
import { Component, OnInit} from '@angular/core';
import { FormGroup, FormBuilder} from "@angular/forms";


// services
import { ActivatedRoute} from "@angular/router";
import { MonitoringObjectService } from "../../services/monitoring-object.service";
import { ConfigService } from "../../services/config.service";
import { MapService } from '@geonature_common/map/map.service'
import { AuthService, User } from "@geonature/components/auth/auth.service";


@Component({
  selector: 'pnx-object',
  templateUrl: './monitoring-object.component.html',
  styleUrls: ['./monitoring-object.component.css']
})
export class MonitoringObjectComponent implements OnInit {

  obj: MonitoringObject;

  backendUrl: string;
  frontendModuleMonitoringUrl: string;

  objForm: FormGroup;

  bEdit = false;
  bLoadingModal = false;

  circuitPointSelected;
  currentUser: User;
  
  childrenTypeStatus: boolean;

  childrenStatus = {}

  constructor(
    private _route: ActivatedRoute,
    private _objService: MonitoringObjectService,
    private _configService: ConfigService,
    private _formBuilder: FormBuilder,
    public mapservice: MapService,
    private _auth: AuthService,
  ) { }

  ngOnInit() {

    this.currentUser = this._auth.getCurrentUser();

    this._route.paramMap
      .flatMap((params) => {
        this.bLoadingModal = true; // affiche la fenetre de chargement
        
        this.initParams(params)

        return this._configService.init(this.obj.modulePath);
      })
      .flatMap(() => {
        this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl()
        this.backendUrl = this._configService.backendUrl()
        return Observable.forkJoin(this.obj.get(1), this.obj.getParent(1)); // TODO
      })
      .flatMap(() =>  {
        return this.obj.getCircuitPoints(); //TODO
      })
      .subscribe(() => {
        this.obj.initTemplate()
        console.log('info', `Objet chargé ${this.obj.objectType} ${this.obj.modulePath}`);
        this.bLoadingModal = false;
        this.obj.bIsInitialized = true;
      });
  }

  initParams(params) {
    this.objForm = this._formBuilder.group({});
    let objectType = params.get('objectType') ? params.get('objectType') : 'module';
    let modulePath = params.get('modulePath');
    let id = params.get('id');
    let parentId = params.get('parentId');

    this.obj = new MonitoringObject(modulePath, objectType, id, this._objService);
    this.obj.parentId = parentId;

    // si on est sur une création (pas d'id et id_parent ou pas de module_path pour module (root))
    this.bEdit = (this.obj.isRoot() && !modulePath) || (!this.obj.id && !!this.obj.parentId);

  }

  initData() {

  }

}
