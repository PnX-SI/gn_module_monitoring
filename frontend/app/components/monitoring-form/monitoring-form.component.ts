import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators, FormControl } from '@angular/forms';
import { MonitoringObject } from '../../class/monitoring-object';
// import { Router } from "@angular/router";
import { ConfigService } from '../../services/config.service';
import { DataUtilsService } from '../../services/data-utils.service';
import { CommonService } from '@geonature_common/service/common.service';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';
import { ActivatedRoute } from '@angular/router';
import { JsonData } from '../../types/jsondata';
import { SitesService } from '../../services/api-geom.service';
import {
  concatMap,
  distinctUntilChanged,
  exhaustMap,
  mergeMap,
  switchMap,
  tap,
  toArray,
} from 'rxjs/operators';
import { EMPTY, from, iif, of } from 'rxjs';
import { FormService } from '../../services/form.service';
import { Router } from '@angular/router';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { GeoJSONService } from '../../services/geojson.service';

@Component({
  selector: 'pnx-monitoring-form',
  templateUrl: './monitoring-form.component.html',
  styleUrls: ['./monitoring-form.component.css'],
})
export class MonitoringFormComponent implements OnInit {
  @Input() currentUser;

  @Input() objForm: FormGroup;

  @Input() obj: MonitoringObject;
  @Output() objChanged = new EventEmitter<MonitoringObject>();

  @Input() objectsStatus;
  @Output() objectsStatusChange = new EventEmitter<Object>();

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() sites: {};

  searchSite = '';

  objFormsDefinition;

  meta: {};

  objFormDynamic: FormGroup = this._formBuilder.group({});
  objFormsDefinitionDynamic;
  typesSiteConfig: JsonData = {};
  schemaUpdate = {};
  idsTypesSite: number[] = [];
  lastGeom = {};
  dataComplement = {};
  schemaGeneric = {};

  public bSaveSpinner = false;
  public bSaveAndAddChildrenSpinner = false;
  public bDeleteSpinner = false;
  public bDeleteModal = false;
  public bChainInput = false;
  public bAddChildren = false;
  public chainShow = [];

  public queryParams = {};

  geomCalculated: boolean = false;
  canDelete: boolean;
  canUpdate: boolean;
  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;

  constructor(
    private _formBuilder: FormBuilder,
    private _route: ActivatedRoute,
    private _configService: ConfigService,
    private _commonService: CommonService,
    private _dataUtilsService: DataUtilsService,
    private _dynformService: DynamicFormService,
    private _siteService: SitesService,
    private _formService: FormService,
    private _router: Router,
    private _geojsonService: GeoJSONService
  ) {}

  ngOnInit() {
    this.initPermission();
    this._configService
      .init(this.obj.moduleCode)
      .pipe(
        mergeMap(() =>
          iif(
            () => this.obj.objectType == 'site' && this.obj.id != undefined,
            this._siteService.getTypesSiteByIdSite(this.obj.id),
            of(null)
          )
        )
      )
      .subscribe((typesSites) => {
        // return this._route.queryParamMap;
        // })
        // .subscribe((queryParams) => {
        this.queryParams = this._route.snapshot.queryParams || {};
        this.bChainInput = this._configService.frontendParams()['bChainInput'];
        this.schemaGeneric = this.obj.schema();
        this.obj.objectType == 'site' ? delete this.schemaGeneric['types_site'] : null;
        this.obj.id != undefined && this.obj.objectType == 'site'
          ? this.initExtraSchema(typesSites)
          : null;
        // init objFormsDefinition

        const schema = this.schemaGeneric;
        // meta pour les parametres dynamiques
        // ici pour avoir acces aux nomenclatures
        this.meta = {
          nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
          dataset: this._dataUtilsService.getDataUtil('dataset'),
          id_role: this.currentUser.id_role,
          bChainInput: this.bChainInput,
          parents: this.obj.parents,
        };
        this.objFormsDefinition = this._dynformService
          .formDefinitionsdictToArray(schema, this.meta)
          .filter((formDef) => formDef.type_widget)
          .sort((a, b) => {
            // medias à la fin
            return a.attribut_name === 'medias' ? +1 : b.attribut_name === 'medias' ? -1 : 0;
          });

        // display_form pour customiser l'ordre dans le formulaire
        // les éléments de display form sont placé en haut dans l'ordre du tableau
        // tous les éléments non cachés restent affichés
        let displayProperties = [...(this.obj.configParam('display_properties') || [])];
        if (displayProperties && displayProperties.length) {
          displayProperties.reverse();
          this.objFormsDefinition.sort((a, b) => {
            let indexA = displayProperties.findIndex((e) => e == a.attribut_name);
            let indexB = displayProperties.findIndex((e) => e == b.attribut_name);
            return indexB - indexA;
          });
        }

        // champs patch pour simuler un changement de valeur et déclencher le recalcul des propriété
        // par exemple quand bChainInput change
        this.objForm.addControl('patch_update', this._formBuilder.control(0));

        // set geometry
        if (this.obj.config['geometry_type']) {
          const validatorRequired =
            this.obj.objectType == 'sites_group'
              ? this._formBuilder.control('')
              : this._formBuilder.control('', Validators.required);
          let frmCtrlGeom = {
            frmCtrl: validatorRequired,
            frmName: 'geometry',
          };
          this.addGeomFormCtrl(frmCtrlGeom);
          // this.objForm.addControl('geometry', this._formBuilder.control('', Validators.required));
        }

        this.geomCalculated = this.obj.properties.hasOwnProperty('is_geom_from_child')
          ? this.obj.properties['is_geom_from_child']
          : false;
        this.geomCalculated ? (this.obj.geometry = null) : null;
        this.bEdit
          ? (this._geojsonService.removeAllFeatureGroup(),
            this._geojsonService.setCurrentmapData(this.obj.geometry, this.geomCalculated))
          : null;
        // pour donner la valeur de idParent
        this.obj.objectType == 'site' ? this.initObjFormDef() : null;
        this.obj.objectType == 'site' ? this.firstInitForm() : this.initForm();
      });
  }

  /** pour réutiliser des paramètres déjà saisis */
  keepDefinitions() {
    return this.objFormsDefinition.filter((def) =>
      this.obj.configParam('keep').includes(def.attribut_name)
    );
  }

  setQueryParams() {
    // par le biais des parametre query de route on donne l'id du ou des parents
    // permet d'avoir un 'tree' ou un objet est sur plusieurs branches
    // on attend des ids d'où test avec parseInt
    for (const key of Object.keys(this.queryParams)) {
      const strToInt = parseInt(this.queryParams[key]);
      if (!Number.isNaN(strToInt)) {
        this.obj.properties[key] = strToInt;
      }
    }
  }

  /** initialise le formulaire quand le formulaire est prêt ou l'object est prêt */
  initForm() {
    if (!(this.objForm && this.obj.bIsInitialized)) {
      return;
    }

    this.setQueryParams();

    // pour donner la valeur de l'objet au formulaire
    this.obj.formValues().subscribe((formValue) => {
      this.objForm.patchValue(formValue);
      this.setDefaultFormValue();
      // reset geom ?
    });
  }

  firstInitForm() {
    if (
      !(this.objFormDynamic && this.obj.bIsInitialized) &&
      !(this.objForm && this.obj.bIsInitialized)
    ) {
      return;
    }

    this.setQueryParams();
    // pour donner la valeur de l'objet au formulaire
    this.obj
      .formValues()
      .pipe(
        exhaustMap((formValue) => {
          this.objForm.patchValue(formValue);
          this.setDefaultFormValue();
          return of(true);
        }),
        concatMap(() => {
          return this.obj.formValues(this.schemaUpdate);
        })
      )
      .subscribe((formValue) => {
        formValue.types_site = this.idsTypesSite;
        // this.objFormDynamic.disable();
        this.objFormDynamic.patchValue(formValue, { onlySelf: true, emitEvent: false });
        // this.objFormDynamic.enable();
      });
  }

  initFormDynamic() {
    if (!(this.objFormDynamic && this.obj.bIsInitialized)) {
      return;
    }
    // pour donner la valeur de l'objet au formulaire
    this.obj.formValues(this.schemaUpdate).subscribe((formValue) => {
      formValue.types_site = this.idsTypesSite;
      // this.objFormDynamic.disable();
      this.objFormDynamic.patchValue(formValue, { onlySelf: true, emitEvent: false });
      // this.objFormDynamic.enable();
      // reset geom ?
    });
  }
  keepNames() {
    return this.obj.configParam('keep') || [];
  }

  resetObjForm() {
    // quand on enchaine les relevés
    const chainShow = this.obj.configParam('chain_show');
    if (chainShow) {
      this.chainShow.push(chainShow.map((key) => this.obj.resolvedProperties[key]));
      this.chainShow.push(this.obj.resolvedProperties);
    }

    // les valeur que l'on garde d'une saisie à l'autre
    const keep = {};
    for (const key of this.keepNames()) {
      keep[key] = this.obj.properties[key];
    }

    // nouvel object
    this.obj = new MonitoringObject(
      this.obj.moduleCode,
      this.obj.objectType,
      null,
      this.obj.monitoringObjectService()
    );
    this.obj.init({});

    this.obj.properties[this.obj.configParam('id_field_Name')] = null;

    // pq get ?????
    // this.obj.get(0).subscribe(() => {
    this.obj.bIsInitialized = true;
    for (const key of this.keepNames()) {
      this.obj.properties[key] = keep[key];
    }

    this.objChanged.emit(this.obj);
    this.objForm.patchValue({ geometry: null });
    this.initForm();
    // });
  }

  /** Pour donner des valeurs par defaut si la valeur n'est pas définie
   * id_digitiser => current_user.id_role
   * id_inventor => current_user.id_role
   * observers => [current_user.id_role]
   * date => today
   */
  setDefaultFormValue() {
    const value = this.objForm.value;
    const date = new Date();
    const defaultValue = {
      id_digitiser: value['id_digitiser'] || this.currentUser.id_role,
      id_inventor: value['id_inventor'] || this.currentUser.id_role,
      observers: value['observers'] || [this.currentUser.id_role],
      first_use_date: value['first_use_date'] || {
        year: date.getUTCFullYear(),
        month: date.getUTCMonth() + 1,
        day: date.getUTCDate(),
      },
    };
    this.objForm.patchValue(defaultValue);
  }

  /**
   * TODO faire des fonctions dans monitoring objet (ou moniotring objet service pour naviguer
   */

  /**
   * Valider et renseigner les enfants
   */
  navigateToAddChildren() {
    this.bEditChange.emit(false);
    this.obj.navigateToAddChildren();
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToDetail() {
    this.bEditChange.emit(false); // patch bug navigation
    this.obj.navigateToDetail();
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToParent() {
    this.bEditChange.emit(false); // patch bug navigation
    this.obj.navigateToParent();
  }

  msgToaster(action) {
    return `${action} ${this.obj.labelDu()} ${this.obj.description()} effectuée`.trim();
  }

  /** TODO améliorer site etc.. */
  onSubmit(isAddChildrend = false) {
    isAddChildrend
      ? (this.bSaveAndAddChildrenSpinner = this.bAddChildren = true)
      : (this.bSaveSpinner = true);
    if (this.obj.objectType == 'site') {
      this.dataComplement = { ...this.typesSiteConfig, types_site: this.idsTypesSite };
    }
    let objFormValueGroup = {};
    this.obj.objectType == 'site'
      ? (objFormValueGroup = { ...this.objForm.value, ...this.objFormDynamic.value })
      : (objFormValueGroup = this.objForm.value);
    this.obj.objectType == 'site'
      ? Object.assign(this.obj.config['specific'], this.schemaUpdate)
      : null;
    const action = this.obj.id
      ? this.obj.patch(objFormValueGroup, this.dataComplement)
      : this.obj.post(objFormValueGroup, this.dataComplement);
    const actionLabel = this.obj.id ? 'Modification' : 'Création';
    action.subscribe((objData) => {
      this._commonService.regularToaster('success', this.msgToaster(actionLabel));
      this.bSaveSpinner = this.bSaveAndAddChildrenSpinner = false;
      this.objChanged.emit(this.obj);

      /** si c'est un module : reset de la config */
      if (this.obj.objectType === 'module') {
        this._configService.loadConfig(this.obj.moduleCode).subscribe();
      }

      if (this.bChainInput) {
        this.resetObjForm();
      } else if (this.bAddChildren) {
        this.navigateToAddChildren();
      } else {
        if (this.obj.configParam('redirect_to_parent')) {
          this.navigateToParent();
        } else {
          this.navigateToDetail();
        }
      }
    });
  }

  onCancelEdit() {
    if (this.obj.id) {
      const urlTree = this._router.parseUrl(this._router.url);
      const urlWithoutParams = urlTree.root.children['primary'].segments
        .map((it) => it.path)
        .join('/');
      this._router.navigate([urlWithoutParams]);

      // this._geojsonService.removeAllFeatureGroup();
      this.obj.geometry == null
        ? this._geojsonService.setMapDataWithFeatureGroup([this._geojsonService.sitesFeatureGroup])
        : this._geojsonService.setMapBeforeEdit(this.obj.geometry);
      this.bEditChange.emit(false);
    } else {
      this.navigateToParent();
    }
  }

  onDelete() {
    this.bDeleteSpinner = true;
    this.obj.delete().subscribe((objData) => {
      this.bDeleteSpinner = this.bDeleteModal = false;
      this.obj.deleted = true;
      this.objChanged.emit(this.obj);
      this._commonService.regularToaster('info', this.msgToaster('Suppression'));
      setTimeout(() => {
        this.navigateToParent();
      }, 100);
    });
  }

  onObjFormValueChange(event) {
    // Check si types_site est modifié
    const change = this.obj.change();
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objForm, meta: this.meta });
    }, 100);
  }

  onObjFormValueChangeDynamic(event) {
    // Check si types_site est modifié
    if (event.types_site != null && event.types_site.length != this.idsTypesSite.length) {
      this.checkChangedTypeSite();
    }
    const change = this.obj.change();
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objForm, meta: this.meta });
    }, 100);
  }

  procesPatchUpdateForm() {
    this.objForm.patchValue({ patch_update: this.objForm.value.patch_update + 1 });
  }

  /** bChainInput gardé dans config service */
  bChainInputChanged() {
    for (const formDef of this.objFormsDefinition) {
      formDef.meta.bChainInput = this.bChainInput;
    }
    this._configService.setFrontendParams('bChainInput', this.bChainInput);
    // patch pour recalculers
    this.procesPatchUpdateForm();
  }

  initExtraSchema(typeSiteObj) {
    let keysConfigToExclude: string[] = [];
    for (const typeSite of typeSiteObj) {
      this.idsTypesSite.push(typeSite.id_nomenclature_type_site);
      this.typesSiteConfig[typeSite.label] = typeSite;
      if (this.typesSiteConfig[typeSite.label].config?.specific) {
        keysConfigToExclude.push(
          ...Object.keys(this.typesSiteConfig[typeSite.label].config.specific)
        );
        Object.assign(this.schemaUpdate, this.typesSiteConfig[typeSite.label].config.specific);
      }
    }
    if (!this.obj.id) {
      this.schemaUpdate = keysConfigToExclude
        .filter((key) => !Object.keys(this.schemaGeneric).includes(key))
        .reduce((obj, key) => {
          obj[key] = this.schemaUpdate[key];
          return obj;
        }, {});
    }

    this.schemaGeneric = Object.keys(this.schemaGeneric)
      .filter((key) => !keysConfigToExclude.includes(key))
      .reduce((obj, key) => {
        obj[key] = this.schemaGeneric[key];
        return obj;
      }, {});
  }

  checkChangedTypeSite() {
    if ('types_site' in this.objFormDynamic.controls) {
      this.objFormDynamic.controls['types_site'].valueChanges
        .pipe(
          distinctUntilChanged(),
          switchMap((idsTypesSite) =>
            iif(
              () => idsTypesSite == undefined || idsTypesSite.length == 0,
              of(null),
              from(idsTypesSite).pipe(
                mergeMap((idTypeSite: number) => {
                  return this._siteService.getTypesSiteById(idTypeSite);
                }),
                toArray()
              )
            )
          )
        )
        .subscribe(
          (typeSiteArray) => {
            if (typeSiteArray == null) {
              this.removExtrForm();
            } else {
              for (const typeSite of typeSiteArray) {
                this.typesSiteConfig[typeSite.label] = typeSite;
              }
              this.updateObj();
            }
          },
          (err) => {
            console.log(err);
          }
        );
    }
  }

  updateObj() {
    this.dataComplement = {};
    const currentIdsTypeSite = this.objFormDynamic.controls.types_site.value;
    let schema = {};
    let objKeysFormToRemove: string[] = [];
    let objKeysFormToAdd = [];
    let schemObjToUpdate = {};
    let objFormToAdd = {};
    let htmlToIgnore: string[] = [];
    if (this.idsTypesSite.length == 0) {
      schema = this.schemaUpdate;
      this.idsTypesSite = [];
      for (const keysType of Object.keys(this.typesSiteConfig)) {
        for (const keysConfig of Object.keys(this.typesSiteConfig[keysType].config.specific)) {
          if (this.typesSiteConfig[keysType].config.specific[keysConfig].type_widget != 'html') {
            objFormToAdd[keysConfig] = null;
          }
          // schema[keysConfig] = this.typesSiteConfig[keysType].config.specific[keysConfig]
        }
        Object.assign(schema, this.typesSiteConfig[keysType].config.specific);
        let idNomencalature = this.typesSiteConfig[keysType]['id_nomenclature_type_site'];
        this.idsTypesSite.push(idNomencalature);
      }
      this.objFormDynamic.disable();
      this.objFormDynamic.patchValue(objFormToAdd, { onlySelf: true, emitEvent: false });
      this.objFormDynamic.enable();
    } else if (
      this.idsTypesSite.length > 0 &&
      currentIdsTypeSite.length < this.idsTypesSite.length
    ) {
      schema = {};
      const schemaObj = this.obj.schema();
      schema['types_site'] = schemaObj['types_site'];
      let newTypeSiteConfig = {};
      for (const keysType of Object.keys(this.typesSiteConfig)) {
        // for (const keysConfig of Object.keys(this.typesSiteConfig[keysType].config.specific)){
        if (
          !currentIdsTypeSite.includes(this.typesSiteConfig[keysType]['id_nomenclature_type_site'])
        ) {
          objKeysFormToRemove.push(...Object.keys(this.typesSiteConfig[keysType].config.specific));
        } else {
          newTypeSiteConfig[keysType] = this.typesSiteConfig[keysType];
          newTypeSiteConfig['types_site'] =
            this.typesSiteConfig[keysType]['id_nomenclature_type_site'];
          Object.assign(schema, this.typesSiteConfig[keysType].config.specific);
        }
      }
      this.idsTypesSite = this.idsTypesSite.filter((elem) => currentIdsTypeSite.includes(elem));
      const objFiltered = Object.keys(this.objFormDynamic.value)
        .filter((key) => !objKeysFormToRemove.includes(key))
        .reduce((obj, key) => {
          obj[key] = this.objFormDynamic.value[key];
          return obj;
        }, {});
      this.typesSiteConfig = newTypeSiteConfig;
      this.objFormDynamic.disable();
      this.objFormDynamic.patchValue(objFiltered, { onlySelf: true, emitEvent: false });
      this.objFormDynamic.enable();
    } else {
      schema = this.schemaUpdate;
      for (const keysType of Object.keys(this.typesSiteConfig)) {
        for (const keysConfig of Object.keys(this.typesSiteConfig[keysType].config.specific)) {
          if (this.typesSiteConfig[keysType].config.specific[keysConfig].type_widget == 'html')
            htmlToIgnore.push(keysConfig);
        }
        objKeysFormToAdd.push(...Object.keys(this.typesSiteConfig[keysType].config.specific));
        Object.assign(schemObjToUpdate, this.typesSiteConfig[keysType].config.specific);
      }
      const schemaObjFilter = Object.keys(schemObjToUpdate)
        .filter((key) => !Object.keys(schema).includes(key) && key)
        .reduce((obj, key) => {
          obj[key] = schemObjToUpdate[key];
          return obj;
        }, {});

      Object.assign(schema, schemaObjFilter);
      this.idsTypesSite = currentIdsTypeSite;
      const objFormToAdd = objKeysFormToAdd
        .filter((key) => !Object.keys(this.objFormDynamic.value).includes(key))
        .reduce((obj, key) => {
          obj[key] = null;
          return obj;
        }, {});
      Object.keys(objFormToAdd).length == 0
        ? null
        : (this.objFormDynamic.disable(),
          this.objFormDynamic.patchValue(objFormToAdd, { onlySelf: true, emitEvent: false }),
          this.objFormDynamic.enable());
    }

    this.initObjFormDef(schema);
    // this.objFormsDefinitionDynamic = this._dynformService
    //   .formDefinitionsdictToArray(schema, this.meta)
    //   .filter((formDef) => formDef.type_widget)
    //   .sort((a, b) => {
    //     // medias à la fin
    //     return a.attribut_name === 'medias' ? +1 : b.attribut_name === 'medias' ? -1 : 0;
    //   });

    // display_form pour customiser l'ordre dans le formulaire
    // les éléments de display form sont placé en haut dans l'ordre du tableau
    // tous les éléments non cachés restent affichés
    let displayProperties = [...(this.obj.configParam('display_properties') || [])];
    if (displayProperties && displayProperties.length) {
      displayProperties.reverse();
      this.objFormsDefinitionDynamic.sort((a, b) => {
        let indexA = displayProperties.findIndex((e) => e == a.attribut_name);
        let indexB = displayProperties.findIndex((e) => e == b.attribut_name);
        return indexB - indexA;
      });
      // this.initForm()
    }
    this.dataComplement = { ...this.typesSiteConfig, types_site: this.idsTypesSite };
  }

  removExtrForm() {
    this.schemaUpdate = {};
    let objKeysFormToRemove: string[] = [];
    const currentIdsTypeSite = this.objFormDynamic.controls.types_site.value;
    // Cas ou plus aucun types site
    if (currentIdsTypeSite.length == 0) {
      this.idsTypesSite = [];
      for (const keysType of Object.keys(this.typesSiteConfig)) {
        if (keysType != 'types_site') {
          objKeysFormToRemove.push(...Object.keys(this.typesSiteConfig[keysType].config.specific));
        }
      }
    }

    const objFiltered = Object.keys(this.objFormDynamic.value)
      .filter((key) => !objKeysFormToRemove.includes(key))
      .reduce((obj, key) => {
        obj[key] = this.objFormDynamic.value[key];
        return obj;
      }, {});

    this.initObjFormDef();

    this.objFormDynamic.disable();
    this.objFormDynamic.patchValue(objFiltered, { onlySelf: true, emitEvent: false });
    this.objFormDynamic.enable();
    this.typesSiteConfig = {};
    this.dataComplement = {};
  }

  initObjFormDef(schema = null) {
    if (schema) {
      this.schemaUpdate = schema;
    } else {
      const schema = this.obj.schema();
      this.schemaUpdate['types_site'] = schema['types_site'];
    }

    this.objFormsDefinitionDynamic = this._dynformService
      .formDefinitionsdictToArray(this.schemaUpdate, this.meta)
      .filter((formDef) => formDef.type_widget)
      .sort((a, b) => {
        return a.attribut_name === 'types_site' ? -1 : b.attribut_name === 'types_site' ? +1 : 0;
      });
  }

  initPermission() {
    this.canDelete =
      this.obj.objectType == 'module'
        ? this.currentUser?.moduleCruved[this.obj.objectType]['D'] > 0
        : this.obj.cruved['D'];
    this.canUpdate =
      this.obj.objectType == 'module'
        ? this.currentUser?.moduleCruved[this.obj.objectType]['U'] > 0
        : this.obj.cruved['U'];
  }

  notAllowedMessage() {
    this._commonService.translateToaster(
      'warning',
      "Vous n'avez pas les permissions nécessaires pour éditer l'objet"
    );
  }

  addGeomFormCtrl(frmCtrl: { frmCtrl: FormControl; frmName: string }) {
    if (frmCtrl.frmName in this.objForm.controls) {
    } else {
      this.objForm.addControl(frmCtrl.frmName, frmCtrl.frmCtrl);
    }
  }

  ngOnDestroy() {
    this.objForm.patchValue({ geometry: null });
  }
}
