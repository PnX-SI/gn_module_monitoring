import { Observable, of, forkJoin } from "@librairies/rxjs";
import { mergeMap } from "@librairies/rxjs/operators";

import { MonitoringObject } from '../../class/monitoring-object';
import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder } from "@angular/forms";


// services
import { ActivatedRoute } from "@angular/router";
import { MonitoringObjectService } from "../../services/monitoring-object.service";
import { ConfigService } from "../../services/config.service";
import { DataUtilsService } from "../../services/data-utils.service";
import { MapService } from '@geonature_common/map/map.service'
import { AuthService, User } from "@geonature/components/auth/auth.service";

import {Utils} from '../../utils/utils'
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

  currentUser: User;

  objectsStatus: Object = {};

  constructor(
    private _route: ActivatedRoute,
    private _objService: MonitoringObjectService,
    private _configService: ConfigService,
    private _dataUtilsService: DataUtilsService,
    private _formBuilder: FormBuilder,
    public mapservice: MapService,
    private _auth: AuthService,
  ) { }

  ngOnInit() {

    this.currentUser = this._auth.getCurrentUser();

    this._route.paramMap
      .pipe(
        mergeMap((params) => {
          this.bLoadingModal = true; // affiche la fenetre de chargement
          this.objForm = this._formBuilder.group({}); // mise à zéro du formulaire

          this.initParams(params)
          // chargement de la configuration
          return this._configService.init(this.obj.modulePath);
        }),

        mergeMap(() => {
          return this.initConfig(); // initialisation de la config
        }),

        mergeMap(() => {
          return this.initData(); // recupérations des données Nomenclature, Taxonomie, Utilisateur.. et mise en cache 
        }),

        mergeMap(() => {
          return this.getMonitoringObject(); // récupération des données de l'object selon le type (module, site, etc..)
        })
      )
      .subscribe(() => {
        this.obj.initTemplate() // pour le html
        this.bLoadingModal = false; // fermeture du modal
        this.obj.bIsInitialized = true; // obj initialisé
        // si on est sur une création (pas d'id et id_parent ou pas de module_path pour module (root))
        this.bEdit = (this.obj.isRoot() && !this.obj.modulePath) || (!this.obj.id && !!this.obj.parentId);

        this.initObjectsStatus()

        console.log('info', `Objet chargé ${this.obj.objectType} ${this.obj.modulePath}`);
      });
  }

  initObjectsStatus() {
    const $this = this;
    const objectsStatus = {}
    this.obj.childrenTypes().forEach((childrenType) => {
      objectsStatus[childrenType] = []
      $this.obj.children[childrenType].forEach((child) => {
        objectsStatus[childrenType].push(
          {
            "id": child.id,
            "selected": false,
            "visible": true
          }
        )
      })
    });
  }

  initParams(params) {
    let objectType = params.get('objectType') ? params.get('objectType') : 'module';

    this.obj = new MonitoringObject(params.get('modulePath'),
      objectType,
      params.get('id'),
      this._objService
    );

    this.obj.parentId = params.get('parentId');
  }

  initConfig(): Observable<any> {
    return this._configService.init(this.obj.modulePath)
      .pipe(
        mergeMap(() => {
          this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl()
          this.backendUrl = this._configService.backendUrl();
          return of(true);
        })
      );
  }

  initData(): Observable<any> {
    return this._dataUtilsService.getInitData(this.obj.modulePath);
  }

  getMonitoringObject(): Observable<any> {
    // TODO mettre au propre
    return forkJoin(this.obj.get(1));
  }

}
