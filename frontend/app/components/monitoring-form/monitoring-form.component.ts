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
  mergeMap,
  switchMap,
  tap,
  map,
  toArray,
} from 'rxjs/operators';
import { EMPTY, forkJoin, from, iif, of } from 'rxjs';
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

  meta:JsonData = {};

  objFormDynamic: FormGroup = this._formBuilder.group({});
  objFormsDefinitionDynamic;
  typesSiteConfig: JsonData = {};
  specificConfig: JsonData = {};
  confiGenericSpec: JsonData = {};
  schemaUpdate = {};
  idsTypesSite: number[] = [];
  lastGeom = {};
  dataComplement = {};
  schemaGeneric = {};
  // confiGenericSpec = {};

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

  isSiteObject: boolean = false;
  isEditObject: boolean = false;
  displayProperties: string[] = [];

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
        map(()=>{
          this.isSiteObject = this.obj.objectType === 'site';
          this.isEditObject = this.obj.id !== undefined;
        }
        ),
        switchMap(() =>
        // Initialisation des config 
          iif(
            () => this.isSiteObject && this.isEditObject ,
            this.initTypeSiteConfig(
              this.obj.config['specific'],
              this.obj['properties'],
              this.obj.config['types_site']
            ).pipe(
              concatMap(({ idsTypesSite, typesSiteConfig }) => {
                this.idsTypesSite = idsTypesSite;
                this.typesSiteConfig = typesSiteConfig;
                return this.initSpecificConfig(
                  this.obj.config['specific'],
                  this.obj.config['types_site']
                );
              }),
              concatMap((specificConfig) => {
                this.specificConfig = specificConfig;
                this.confiGenericSpec = this.mergeObjects(this.specificConfig, this.obj.config['generic'])
                return EMPTY
              })
            ),
            this.initSpecificConfig(this.obj.config['specific']).pipe(
              concatMap((specificConfig) => {
                this.specificConfig = specificConfig;
                this.confiGenericSpec = this.mergeObjects(this.specificConfig, this.obj.config['generic'])
                return EMPTY
              })
            )
          )
        ),
        map((_)=> {
          // Initialisation des variables queryParams , bChainInput
          this.queryParams = this._route.snapshot.queryParams || {};
          this.bChainInput = this._configService.frontendParams()['bChainInput'];
          this.meta = {
            nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
            dataset: this._dataUtilsService.getDataUtil('dataset'),
            id_role: this.currentUser.id_role,
            bChainInput: this.bChainInput,
            parents: this.obj.parents,
          };
        }),
      concatMap((_) =>
        // Initialisation definition des champs de l'object objForm 
         {this.initObjFormDefiniton(this.confiGenericSpec, this.meta).pipe(
          map((objFormDefinition) =>
          this.objFormsDefinition = objFormDefinition)
         )
         return EMPTY
        }
      ),
      switchMap((_) =>
       // Initialisation definition des champs de l'object objFormDynamic
        iif(
          () => this.isSiteObject && this.isEditObject ,
          this.initObjFormDefiniton(this.typesSiteConfig,this.meta).pipe(
              map((objFormDefinition) =>{
              this.objFormsDefinition = objFormDefinition
              return EMPTY})
             )
          ,
          EMPTY
        )
        ), 
      concatMap((_) => {
        // Initialisation de l'ordre d'affichage des champs objForDefinition
        this.displayProperties = [...(this.obj.configParam('display_properties') || [])];
        this.sortObjFormDefinition(this.displayProperties, this.objFormsDefinition).pipe(
            tap(objFormsDefinition => this.objFormsDefinition = objFormsDefinition)
        )
        return EMPTY
      }),
      switchMap((_) =>
      // Initialisation definition des champs de l'object objFormDynamic
       iif(
         () => this.isSiteObject && this.isEditObject ,
         this.sortObjFormDefinition(this.displayProperties,this.objFormsDefinition).pipe(
          tap(objFormsDefinitionDynamic => this.objFormsDefinitionDynamic = objFormsDefinitionDynamic)
        )
         ,
         EMPTY
       )
       ),
       concatMap(() => {
        // Ajout du champ géométrique à l'object form et du champ patch
        return this.addFormCtrlToObjForm({ frmCtrl: this._formBuilder.control(0), frmName: 'patch_update' }, this.objForm).pipe(
          concatMap((objForm) => {
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
              return this.addFormCtrlToObjForm(frmCtrlGeom, objForm)
            }
            return of(objForm);
          })
        )}),
          concatMap((objForm) => {
             return this.setQueryParams(this.obj)
          }),
          concatMap((obj) => {
            this.obj = obj
            // On match les valeurs de l'objet en lien avec l'object Form et ensuite on patch l'object form
            return forkJoin([
              this.initObjFormValues(this.obj, this.confiGenericSpec,this.idsTypesSite),
              iif(
                () => this.isSiteObject,
                this.initObjFormSpecificValues(this.obj, this.typesSiteConfig),
                of(null)
              )
            ]).pipe(
              tap(([genericFormValues, specificFormValues]) => {
                this.objForm.patchValue(genericFormValues);
                if (specificFormValues !== null) {
                  this.objFormDynamic.patchValue(specificFormValues)
                }
              })
            );
          })
        )
      .subscribe((objForm) => {
        console.log(objForm)
        // this.specificConfig = specificConfig;
        // return this._route.queryParamMap;
        // })
        // .subscribe((queryParams) => {
        // this.queryParams = this._route.snapshot.queryParams || {};
        // this.bChainInput = this._configService.frontendParams()['bChainInput'];
        // NOTES: ici schemaGeneric = this.obj.config.generic
        // this.schemaGeneric = this.obj.schema();

        // TODO: utilisé cette manière et plus besoin de mettre à jour le schema Generic
        // this.confiGenericSpec = this.obj.config['generic'];
        // this.obj.objectType == 'site' ? delete this.schemaGeneric['types_site'] : null;
        // this.obj.id != undefined && this.obj.objectType == 'site' ? this.initExtraSchema() : null;
        // init objFormsDefinition

        // NOTES: ici schemaGeneric = this.obj.config.generic
        // const schema = this.confiGenericSpec;
        // meta pour les parametres dynamiques
        // ici pour avoir acces aux nomenclatures
        // this.meta = {
        //   nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
        //   dataset: this._dataUtilsService.getDataUtil('dataset'),
        //   id_role: this.currentUser.id_role,
        //   bChainInput: this.bChainInput,
        //   parents: this.obj.parents,
        // };
        // this.objFormsDefinition = this._dynformService
        //   .formDefinitionsdictToArray(schema, this.meta)
        //   .filter((formDef) => formDef.type_widget)
        //   .sort((a, b) => {
        //     if (a.attribut_name === 'types_site') return 1;
        //     if (b.attribut_name === 'types_site') return -1;
        //     if (a.attribut_name === 'medias') return 1;
        //     if (b.attribut_name === 'medias') return -1;
        //     return 0;
        //   });

        // display_form pour customiser l'ordre dans le formulaire
        // les éléments de display form sont placé en haut dans l'ordre du tableau
        // tous les éléments non cachés restent affichés
        // let displayProperties = [...(this.obj.configParam('display_properties') || [])];
        // if (displayProperties && displayProperties.length) {
        //   displayProperties.reverse();
        //   this.objFormsDefinition.sort((a, b) => {
        //     let indexA = displayProperties.findIndex((e) => e == a.attribut_name);
        //     let indexB = displayProperties.findIndex((e) => e == b.attribut_name);
        //     return indexB - indexA;
        //   });
        // }

        // champs patch pour simuler un changement de valeur et déclencher le recalcul des propriété
        // par exemple quand bChainInput change
        // this.objForm.addControl('patch_update', this._formBuilder.control(0));

        // // set geometry
        // if (this.obj.config['geometry_type']) {
        //   const validatorRequired =
        //     this.obj.objectType == 'sites_group'
        //       ? this._formBuilder.control('')
        //       : this._formBuilder.control('', Validators.required);
        //   let frmCtrlGeom = {
        //     frmCtrl: validatorRequired,
        //     frmName: 'geometry',
        //   };
        //   this.addGeomFormCtrl(frmCtrlGeom);
        //   // this.objForm.addControl('geometry', this._formBuilder.control('', Validators.required));
        // }

        // this.geomCalculated = this.obj.properties.hasOwnProperty('is_geom_from_child')
        //   ? this.obj.properties['is_geom_from_child']
        //   : false;
        // this.geomCalculated ? (this.obj.geometry = null) : null;
        // this.bEdit
        //   ? this._geojsonService.setCurrentmapData(this.obj.geometry, this.geomCalculated)
        //   : null;
        // pour donner la valeur de idParent
        // this.obj.objectType == 'site' ? this.initObjFormDef(this.typesSiteConfig) : null;
        // this.obj.objectType == 'site' ? this.firstInitForm() : this.initForm();
      });
  }

  /** pour réutiliser des paramètres déjà saisis */
  keepDefinitions() {
    return this.objFormsDefinition.filter((def) =>
      this.obj.configParam('keep').includes(def.attribut_name)
    );
  }

  setQueryParams(obj:MonitoringObject) {
    // par le biais des parametre query de route on donne l'id du ou des parents
    // permet d'avoir un 'tree' ou un objet est sur plusieurs branches
    // on attend des ids d'où test avec parseInt
    for (const key of Object.keys(this.queryParams)) {
      const strToInt = parseInt(this.queryParams[key]);
      if (!Number.isNaN(strToInt)) {
        obj.properties[key] = strToInt;
      }
    }
    return of(obj)
  }

  /** initialise le formulaire quand le formulaire est prêt ou l'object est prêt */
  initForm() {
    if (!(this.objForm && this.obj.bIsInitialized)) {
      return;
    }

    // this.setQueryParams();

    // pour donner la valeur de l'objet au formulaire
    // this._formService.formValues(this.obj, this.confiGenericSpec).subscribe((formValue) => {
    //   this.objForm.patchValue(formValue);
    //   this.setDefaultFormValue();
    // });
   this._formService.formValues(this.obj, this.confiGenericSpec)
      .pipe(
        map((genericFormValues) => {
          genericFormValues['types_site'] = this.idsTypesSite;
          return genericFormValues;
        })
      )
      .subscribe((formValue) => {
        this.objForm.patchValue(formValue);
        this.setDefaultFormValue();
      });
  }

  firstInitForm() {
    if (
      !(this.objFormDynamic && this.obj.bIsInitialized) &&
      !(this.objForm && this.obj.bIsInitialized)
    ) {
      return;
    }

    // this.setQueryParams();
    // pour donner la valeur de l'objet au formulaire
    // this._formService
    //   .formValues(this.obj, this.confiGenericSpec)
    //   .pipe(
    //     concatMap((formValue) => {
    //       return { ...formValue, ...this._formService.formValues(this.obj, this.specificConfig)};
    //     }),
    //     concatMap((formValue) => {
    //       this.objForm.patchValue(formValue);
    //       return this._formService.formValues(this.obj, this.typesSiteConfig);
    //     })
    //   )
    //   .subscribe((formValue) => {
    //     formValue['types_site'] =  this.idsTypesSite
    //     // this.objFormDynamic.disable();
    //     this.objFormDynamic.patchValue(formValue, { onlySelf: true, emitEvent: false });
    //     // this.objFormDynamic.enable();
    //   });

      this._formService.formValues(this.obj, this.confiGenericSpec)
      .pipe(
        map((genericFormValues) => {
          genericFormValues['types_site'] = this.idsTypesSite;
          return genericFormValues;
        }),
        concatMap((formValue) => {
          this.objForm.patchValue(formValue);
          return this._formService.formValues(this.obj, this.typesSiteConfig);
        })
      )
      .subscribe((formValue) => {
        this.objFormDynamic.patchValue(formValue, { onlySelf: true, emitEvent: false });
      });
  }

  initFormDynamic() {
    if (!(this.objFormDynamic && this.obj.bIsInitialized)) {
      return;
    }
    // pour donner la valeur de l'objet au formulaire
    this._formService
      .formValues(this.obj, this.typesSiteConfig)
      // .pipe(
      //   map((formValue) => {
      //     formValue.types_site = this.idsTypesSite;
      //     return formValue;
      //   })
      // )
      .subscribe((formValue) => {
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
   * date => today
   */
  setDefaultFormValue() {
    const value = this.objForm.value;
    const date = new Date();
    const defaultValue = {
      id_digitiser: value['id_digitiser'] || this.currentUser.id_role,
      id_inventor: value['id_inventor'] || this.currentUser.id_role,
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

  initExtraSchema() {
    // NOTES: typeSiteObj doit être remplacé par this.obj.config.types_site ( key = id_nomenclature_type_site, value = label et typeSite.label = this.obj.config.types_site[key].name et ensuite il faut boucler sur  les display properties
    //  et voir ce qui match avec les keys de this.obj.config.specific
    // TODO: Chaner la manière de mettre en place le schemaUpdate , idsTypesSite, typesSiteConfig et schemaGeneric
    let keysConfigToExclude: string[] = [];
    const typeSiteObj = this.obj.config['types_site'];
    const propertiesObj = this.obj['properties'];
    const specificConfig = this.obj.config['specific'];
    // for (const typeSite of typeSiteObj) {
    //   //  remplacer typeSite.id_nomenclature_type_site --> key of this.obj.config.types_site
    //   this.idsTypesSite.push(typeSite.id_nomenclature_type_site);
    //   this.typesSiteConfig[typeSite.label] = typeSite;
    //   if (this.typesSiteConfig[typeSite.label].config?.specific) {
    //     keysConfigToExclude.push(
    //       ...Object.keys(this.typesSiteConfig[typeSite.label].config.specific)
    //     );
    //     Object.assign(this.schemaUpdate, this.typesSiteConfig[typeSite.label].config.specific);
    //   }
    // }
    for (const typeSiteConfig in this.typesSiteConfig) {
      keysConfigToExclude.push(...Object.keys(typeSiteConfig));
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

    //TODO: [DEV-SUIVI-EOLIEN] A SUPPRIMER
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
      // this.schemaUpdate['types_site'] = schema['types_site'];
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
        : this.obj.cruved['D'] && !['site', 'sites_group'].includes(this.obj.objectType);
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

  addFormCtrlToObjForm(frmCtrl: { frmCtrl: FormControl; frmName: string }, objForm) {
      if (frmCtrl.frmName in objForm.controls) {
      } else {
        objForm.addControl(frmCtrl.frmName, frmCtrl.frmCtrl);
      }
      return of(objForm)
    }


  initObjFormDefiniton(schema:JsonData,meta:JsonData){
    const objectFormDefiniton = this._dynformService
          .formDefinitionsdictToArray(schema, this.meta)
          .filter((formDef) => formDef.type_widget)
          .sort((a, b) => {
            if (a.attribut_name === 'types_site') return 1;
            if (b.attribut_name === 'types_site') return -1;
            if (a.attribut_name === 'medias') return 1;
            if (b.attribut_name === 'medias') return -1;
            return 0;
          });
     return of(objectFormDefiniton)
  }

  initTypeSiteConfig(configSpecific, properties, configTypesSite) {
    const idsTypesSite = [];
    const typesSiteConfig = {};
    for (const keyTypeSite in configTypesSite) {
      let typeSiteName = configTypesSite[keyTypeSite].name;
      if (properties['types_site'].includes(typeSiteName)) {
        idsTypesSite.push(parseInt(keyTypeSite));
        for (const prop of configTypesSite[keyTypeSite].display_properties) {
          typesSiteConfig[prop] = configSpecific[prop];
        }
      }
    }
    return of({ idsTypesSite, typesSiteConfig });
  }

  initSpecificConfig(configSpecific, configTypesSite = {}) {
    let specificConfig;
    if (configTypesSite) {
      specificConfig = this.getRemainingProperties(this.typesSiteConfig, configSpecific);
    } else {
      specificConfig = configSpecific;
    }
    return of(specificConfig);
  }

  sortObjFormDefinition(displayProperties:string[], objFormDef: JsonData) {
    // let displayProperties = [...(this.obj.configParam('display_properties') || [])];
    if (displayProperties && displayProperties.length) {
      displayProperties.reverse();
      objFormDef.sort((a, b) => {
        let indexA = displayProperties.findIndex((e) => e == a.attribut_name);
        let indexB = displayProperties.findIndex((e) => e == b.attribut_name);
        return indexB - indexA;
      });
    }
    return of(objFormDef)

  }

  initObjFormValues(obj, config, idsTypesSite){
    return this._formService.formValues(obj, config)
      .pipe(
        concatMap((genericFormValues) => {
          if (idsTypesSite.length == 0) {
            genericFormValues['types_site'] = idsTypesSite;
          }
          return of(genericFormValues);
        })
      )
      // .subscribe((formValue) => {
      //   objForm.patchValue(formValue);
      //   // A mettre après
      //   this.setDefaultFormValue();
      // });
  }


  initObjFormSpecificValues(obj, config){
    return this._formService.formValues(obj, config)
  }

  updateTypeSiteConfig() {}

  getRemainingProperties(obj1: JsonData, obj2: JsonData): JsonData {
    const remainingObj: JsonData = {};
    for (let key in obj1) {
      if (!obj2.hasOwnProperty(key) || obj1[key] !== obj2[key]) {
        remainingObj[key] = obj1[key];
      }
    }
    for (let key in obj2) {
      if (!obj1.hasOwnProperty(key) || obj1[key] !== obj2[key]) {
        remainingObj[key] = obj2[key];
      }
    }

    return remainingObj;
  }

  mergeObjects(obj1: JsonData, obj2: JsonData): JsonData {
    const mergedObject: JsonData = { ...obj1 }; // Start with a copy of obj1
    
    // Loop through obj2 and overwrite or add keys to mergedObject
    for (const key in obj2) {
      if (obj2.hasOwnProperty(key)) {
        mergedObject[key] = obj2[key];
      }
    }
    
    return mergedObject;
  }

  ngOnDestroy() {
    this.objForm.patchValue({ geometry: null });
  }
}
