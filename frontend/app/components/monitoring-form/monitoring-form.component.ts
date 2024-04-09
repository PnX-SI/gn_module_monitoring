import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators, FormControl, FormArray, AbstractControl } from '@angular/forms';
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
  reduce,
  filter,
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

  // objFormDynamic: FormGroup = this._formBuilder.group({});
  // objFormsDefinitionDynamic;

  objFormsDynamic: { [key: string]: FormGroup } = {};
  objFormsDefinitionDynamic: { [key: string]: any } = {};

  typesSiteConfig: JsonData = {};
  specificConfig: JsonData = {};
  confiGenericSpec: JsonData = {};
  schemaUpdate = {};
  // idsTypesSite: number[] = [];
 idsTypesSite: Set<number> = new Set<number>();
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
  hasDynamicGroups: boolean = false;

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
          this.isEditObject = this.obj.id !== undefined && this.obj.id !== null;
          console.log("1- CHECK TYPE OBJECT AND EDIT or NOT",  `Object type is ${this.obj.objectType} and is Edit Object ? ${this.isEditObject}`)
          return of(null)
        }
        ),
        switchMap((_) =>
        // Initialisation des config 
          iif(
            () => this.isSiteObject,
            // CONDITION avec types de site
            this.initTypeSiteConfig(
              this.obj.config['specific'],
              this.obj['properties'],
              this.obj.config['types_site']
            ).pipe(
              concatMap(({ idsTypesSite, typesSiteConfig }) => {
                idsTypesSite.forEach(number => this.idsTypesSite.add(number));
                this.typesSiteConfig = typesSiteConfig;
                return this.initSpecificConfig(
                  this.obj.config['specific'],
                  this.obj.config['types_site']
                );
              }),
              concatMap((specificConfig) =>{
                // Initialisation des formGroup Dynamic 
                if(this.isEditObject){
                  for (const typeSite in this.typesSiteConfig){
                    this.addDynamicFormGroup(typeSite)
                  }
                }

                return of(specificConfig)
              }),
              concatMap((specificConfig) => {
                this.specificConfig = specificConfig;
                this.confiGenericSpec = this.mergeObjects(this.specificConfig, this.obj.config['generic'])
                return of(null)
              })
            ),
            // CONDITION sans types de site
            this.initSpecificConfig(this.obj.config['specific']).pipe(
              concatMap((specificConfig) => {
                this.specificConfig = specificConfig;
                this.confiGenericSpec = this.mergeObjects(this.specificConfig, this.obj.config['generic'])
                return of(null)
              })
            )
          )
        ),
        map((_) => {
          // Initialize objForm based on isSiteObject condition
          if (this.isSiteObject) {
            this.objForm = this.createFormWithDynamicGroups();
          } else {
            this.objForm = this.createFormWithoutDynamicGroups();
          }
          return of(null)
        })
      ,
        map((_)=> {
          // Initialisation des variables queryParams , bChainInput
          console.log("Initialisation des variables queryParams , bChainInput")
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
         {  console.log("Initialisation definition des champs de l'object objForm ")
         return this.initObjFormDefiniton(this.confiGenericSpec, this.meta).pipe(
          map((objFormDefinition) => {
            this.objFormsDefinition = objFormDefinition;
            return null; // Return a value to continue the chain
          })
        );
        }
      ),
      switchMap((_) =>
       // Initialisation definition des champs de l'object objFormDynamic
        iif(
          () => this.isSiteObject ,
          from(Object.entries(this.typesSiteConfig)).pipe(
            concatMap(([typeSite, config]) => {
              return this.initObjFormDefiniton(config, this.meta).pipe(
                map((objFormDefinition) => {
                  console.log('Initialization of dynamic form definition for', typeSite, objFormDefinition);
                  this.objFormsDefinitionDynamic[typeSite] = objFormDefinition;
                  return null;
                })
              );
            })
          ),
          of(null)
        )
        ), 
      concatMap((_) => {
        // Initialisation de l'ordre d'affichage des champs objForDefinition
        console.log("Initialisation de l'ordre d'affichage des champs objForDefinition");
        this.displayProperties = [...(this.obj.configParam('display_properties') || [])];
        this.sortObjFormDefinition(this.displayProperties, this.objFormsDefinition).pipe(
            tap(objFormsDefinition => this.objFormsDefinition = objFormsDefinition)
        )
        console.log("this.objFormsDefinition :", this.objFormsDefinition);
        return of(null)
      }),
      switchMap((_) =>
      // Initialisation de l'ordre d'affichage des champs de l'object objFormDynamic
       iif(
         () => this.isSiteObject && this.isEditObject,
         from(Object.entries(this.typesSiteConfig)).pipe(
          concatMap(([typeSite, config]) => {
            return this.sortObjFormDefinition(this.displayProperties,[config]).pipe(
              tap(objFormsDefinitionDynamic => {console.log("Initialisation de l'ordre d'affichage des champs objFormsDefinitionDynamic"),
              this.objFormsDefinitionDynamic[typeSite]=objFormsDefinitionDynamic})
            )
          })
        )
         ,
         of(null)
       )
       ),
       concatMap(() => {
        // Ajout du champ géométrique à l'object form et du champ patch
        console.log("Ajout du champ géométrique à l'object form et du champ patch")
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
            console.log("setQueryParams")
             return this.setQueryParams(this.obj)
          }),
          concatMap((obj) => {
            this.obj = obj
            // On match les valeurs de l'objet en lien avec l'object Form et ensuite on patch l'object form
            console.log(" On match les valeurs de l'objet en lien avec l'object Form et ensuite on patch l'object form")
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
                  this.patchValuesInDynamicGroups(specificFormValues)
                }
              })
            );
          })
        )
      .subscribe((objForm) => {
        console.log(" ObjForm Initialisé")
        console.log(objForm)
        console.log(" ObjFormDynamic Initialisé")
        console.log(this.objFormsDynamic)

        const dynamicGroupsArray = this.objForm.get('dynamicGroups') as FormArray;
        this.subscribeToDynamicGroupsChanges(dynamicGroupsArray);
      });
  }

  subscribeToDynamicGroupsChanges(dynamicGroupsArray: FormArray): void {
    dynamicGroupsArray.valueChanges.subscribe((value) => {
      this.hasDynamicGroups = dynamicGroupsArray.controls.length > 0;
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
      !(this.obj.bIsInitialized) &&
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
    //     // objFormDynamic.disable();
    //     objFormDynamic.patchValue(formValue, { onlySelf: true, emitEvent: false });
    //     // objFormDynamic.enable();
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
        this.patchValuesInDynamicGroups(formValue);
      });
  }

  initFormDynamic(typeSite:string) {
    if (!(this.objFormsDefinition[typeSite] && this.obj.bIsInitialized)) {
      return;
    }
    // pour donner la valeur de l'objet au formulaire
    this._formService
      .formValues(this.obj, this.typesSiteConfig[typeSite])
      // .pipe(
      //   map((formValue) => {
      //     formValue.types_site = this.idsTypesSite;
      //     return formValue;
      //   })
      // )
      .subscribe((formValue) => {
        // objFormDynamic.disable();
        this.patchValuesInDynamicGroups(formValue);
        // objFormDynamic.enable();
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
      ? (objFormValueGroup = this.flattenFormGroup(this.objForm))
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
    if (event.types_site != null && event.types_site.length != this.idsTypesSite.size) {
      this.updateTypeSiteForm().subscribe(
        (_) => {
          this.hasDynamicGroups = true
        }
      );
    }
    const change = this.obj.change();
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objForm, meta: this.meta });
    }, 100);
  }

  onObjFormValueChangeDynamic(event) {

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


  
  updateTypeSiteForm() {
    return this.objForm.controls['types_site'].valueChanges.pipe(
      distinctUntilChanged(),
      switchMap((idsTypesSite) =>
        iif(
          () => idsTypesSite == undefined || idsTypesSite.length == 0,
          of({}),
          from(idsTypesSite).pipe(
            mergeMap((idTypeSite: number) => {
              return of({ [idTypeSite]: this.typesSiteConfig[idTypeSite] });
            }),
            reduce((acc, cur) => ({ ...acc, ...cur }), {})
          )
        )
      ),
      filter(typesSiteObject => !(typesSiteObject === null || Object.keys(typesSiteObject).length === 0)),
      tap((typesSiteObject) => {
        if (typesSiteObject === null || Object.keys(typesSiteObject).length === 0) {
          this.idsTypesSite = new Set<number>();
          this.removeAllDynamicGroups();
        } else {
          for (const [idTypeSite, typeSiteConf] of Object.entries(typesSiteObject)) {
            this.idsTypesSite.add(parseInt(idTypeSite));
            this.typesSiteConfig = Object.keys(this.typesSiteConfig)
              .filter(key => idTypeSite.includes(key))
              .reduce((acc, key) => {
                acc[key] = this.typesSiteConfig[key];
                return acc;
              }, {});
          }
        }
      }),
      concatMap(() => {
        if (this.idsTypesSite.size === 0) {
          return EMPTY; // Skip further processing if idsTypesSite is empty
        }
        return from(Object.entries(this.typesSiteConfig)).pipe(
          concatMap(([typeSite, config]) => {
            return this.initObjFormDefiniton(config, this.meta).pipe(
              map((objFormDefinition) => {
                console.log('Initialization of dynamic form definition for', typeSite, objFormDefinition);
                this.objFormsDefinitionDynamic[typeSite] = objFormDefinition;
                return null;
              })
            );
          })
        );
      }),
      concatMap(()=>{
        return from(Object.entries(this.typesSiteConfig)).pipe(
          concatMap(([typeSite, config]) => {
            return this.addDynamicFormGroup(typeSite);
          })
        );

      }),
      concatMap((_) => {
        return from(Object.entries(this.typesSiteConfig)).pipe(
          concatMap(([typeSite, config]) => {
            return this.sortObjFormDefinition(this.displayProperties, [config]).pipe(
              tap(objFormsDefinitionDynamic => {
                console.log("Initialisation de l'ordre d'affichage des champs objFormsDefinitionDynamic"),
                this.objFormsDefinitionDynamic[typeSite] = objFormsDefinitionDynamic;
              })
            );
          })
        );
      }),
      concatMap((_) => {
        return forkJoin(
          Object.entries(this.typesSiteConfig).map(([typeSite, config]) => {
            return this.initObjFormSpecificValues(this.obj, config).pipe(
              map((formValue) => ({
                typeSite,
                formValue
              }))
            );
          })
        );
      }),
      map((results) => {
        results.forEach(({ typeSite, formValue }) => {
          // Use typeSite and formValue to update objFormsDynamic or patch values in dynamic groups
          this.objFormsDynamic[typeSite].patchValue(formValue)
          // this.patchValuesInDynamicGroups(formValue);
        });
        return results;
      })
    );
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
      typesSiteConfig[keyTypeSite] = {}
      let typeSiteName = configTypesSite[keyTypeSite].name
      if (!this.isEditObject){
        for (const prop of configTypesSite[keyTypeSite].display_properties) {
          typesSiteConfig[keyTypeSite][prop] = configSpecific[prop];
        }
      } else{
        if (properties['types_site'].includes(typeSiteName)) {
          idsTypesSite.push(parseInt(keyTypeSite));
          for (const prop of configTypesSite[keyTypeSite].display_properties) {
            typesSiteConfig[keyTypeSite][prop] = configSpecific[prop];
          }
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
  
  addDynamicFormGroup(groupName: string) {
    const newFormGroup = this._formBuilder.group({});
    this.objFormsDynamic[groupName] = newFormGroup;
  
    // Add form definition for dynamic form group
    this.objFormsDefinitionDynamic[groupName] = {};
  
    // Add new form group to the dynamicGroups FormArray
    if (this.objForm.contains('dynamicGroups')) {
      (this.objForm.get('dynamicGroups') as FormArray).push(newFormGroup);
    }
  
    // Emit the new form group as an Observable
    return of(newFormGroup);
  }

  removeDynamicFormGroup(groupName: string): void {
    // Remove form group from objFormsDynamic
    delete this.objFormsDynamic[groupName];
    delete this.objFormsDefinitionDynamic[groupName];

    // Remove form group from the dynamicGroups FormArray
    const dynamicGroupsArray = this.objForm.get('dynamicGroups') as FormArray;
    const index = dynamicGroupsArray.controls.findIndex(group => group === this.objFormsDynamic[groupName]);
    if (index !== -1) {
      dynamicGroupsArray.removeAt(index);
    }
  }

  removeAllDynamicGroups(): void {
    // Clear objFormsDynamic and objFormsDefinitionDynamic
    this.objFormsDynamic = {};
    this.objFormsDefinitionDynamic = {};
  
    // Clear controls inside dynamicGroups FormArray
    const dynamicGroupsArray = this.objForm.get('dynamicGroups') as FormArray;
    while (dynamicGroupsArray.length) {
      dynamicGroupsArray.removeAt(0); // Remove controls from the beginning
    }
    }


  private createFormWithDynamicGroups(): FormGroup {
    return this._formBuilder.group({
      dynamicGroups: this._formBuilder.array([])
    });
  }

  private createFormWithoutDynamicGroups(): FormGroup {
    return this._formBuilder.group({
    });
  }

  // Method to patch values inside dynamic form groups
patchValuesInDynamicGroups(valuesToPatch: { [key: string]: any }): void {
  Object.keys(this.objFormsDynamic).forEach(groupName => {
    const formGroup = this.objFormsDynamic[groupName];
    if (formGroup instanceof FormGroup) {
      this.patchValuesInFormGroup(formGroup, valuesToPatch);
    }
  });
}

// Method to patch values inside a form group
patchValuesInFormGroup(formGroup: FormGroup, valuesToPatch: { [key: string]: any }): void {
  Object.keys(valuesToPatch).forEach(controlName => {
    if (formGroup.contains(controlName)) {
      formGroup.get(controlName).patchValue(valuesToPatch[controlName]);
    }
  });
}

// Function to flatten a FormGroup into a flat object
flattenFormGroup(formGroup: FormGroup): { [key: string]: any } {
  const flatObject: { [key: string]: any } = {};

  // Recursive function to process nested controls
  const flattenControl = (control: AbstractControl, keyPrefix: string = ''): void => {
    if (control instanceof FormGroup) {
      Object.entries(control.controls).forEach(([controlName, nestedControl]) => {
        flattenControl(nestedControl, `${keyPrefix}${controlName}.`);
      });
    } else if (control instanceof FormArray) {
      control.controls.forEach((arrayControl, index) => {
        flattenControl(arrayControl, `${keyPrefix}[${index}].`);
      });
    } else {
      flatObject[keyPrefix.slice(0, -1)] = control.value;
    }
  };

  // Start flattening from the root FormGroup
  flattenControl(formGroup);

  return flatObject;
};


  ngOnDestroy() {
    this.objForm.patchValue({ geometry: null });
  }
}
