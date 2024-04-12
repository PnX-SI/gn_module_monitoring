import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import {
  FormGroup,
  FormBuilder,
  Validators,
  FormControl,
  FormArray,
  AbstractControl,
} from '@angular/forms';
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
  reduce,
  filter,
  defaultIfEmpty,
  scan,
} from 'rxjs/operators';
import { defer, forkJoin, from, iif, of, Observable } from 'rxjs';
import { FormService } from '../../services/form.service';
import { Router } from '@angular/router';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { GeoJSONService } from '../../services/geojson.service';
import { Utils } from '../../utils/utils';

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

  meta: JsonData = {};

  // objFormDynamic: FormGroup = this._formBuilder.group({});
  // objFormsDefinitionDynamic;

  objFormsDynamic: { [key: string]: FormGroup } = {};
  objFormsDefinitionDynamic: JsonData = {};

  allTypesSiteConfig: JsonData = {};
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
  isInitialzedObjFormDynamic: {keys:string, value: boolean} | {} = {};

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
        switchMap(()=>this.initializeVariables$(this.obj).pipe(
          map(({ isSiteObject, isEditObject, hasDynamicGroups }) => {
            this.isSiteObject = isSiteObject;
            this.isEditObject = isEditObject;
            this.hasDynamicGroups = hasDynamicGroups;
            return isSiteObject
          })
        )),
        switchMap((isSiteObject ) =>
          iif(
            () => isSiteObject,
            this.initializeTypeSiteConfig(this.obj.config['generic'],this.obj.config['specific'],this.obj.config['types_site'],this.obj['properties']['types_site']).pipe(
              map(({specificConfig, confiGenericSpec, allTypesSiteConfig, idsTypesSiteSet}) => {
                this.specificConfig = specificConfig;
                this.confiGenericSpec = confiGenericSpec;
                this.allTypesSiteConfig = allTypesSiteConfig;
                this.idsTypesSite = idsTypesSiteSet
              })
            ),
            this.initializeSpecificConfig(this.obj.config['generic'],this.obj.config['specific']).pipe(
              map(({specificConfig, confiGenericSpec}) => {
                this.specificConfig = specificConfig;
                this.confiGenericSpec = confiGenericSpec;
              })
            )
          )
        ),
        tap(() => {
          if (this.isSiteObject) {
            this._formService.addMultipleFormGroupsToObjForm(this.objFormsDynamic, this.objForm);
          }
        }),
        tap(() => {
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
        switchMap(() => this.initObjFormDefiniton(this.confiGenericSpec, this.meta).pipe(
          map((objFormsDefinition)=>{
            this.objFormsDefinition = objFormsDefinition;
            return objFormsDefinition
          })
        )),
        switchMap((objFormsDefinition) =>
          iif(
            () => this.isSiteObject,
            from(Object.entries(this.allTypesSiteConfig)).pipe(
              concatMap(([typeSite, config]) =>
                this.initObjFormDefiniton(config, this.meta).pipe(
                  map(objFormDefinition => ({ typeSite, objFormDefinition }))
                )
              ),
              concatMap(({ typeSite, objFormDefinition }) =>
                this.sortObjFormDefinition(this.displayProperties, objFormDefinition).pipe(
                  tap(sortedFormDefinition => {
                    console.log(
                      'Initialization of dynamic form definition for',
                      typeSite,
                      sortedFormDefinition
                    );
                    this.objFormsDefinitionDynamic[typeSite] = sortedFormDefinition;
                  })
                )
              )
            ),
            of(null)
          )
        ),
        tap(() => {
          this.displayProperties = [...(this.obj.configParam('display_properties') || [])];
          this.sortObjFormDefinition(this.displayProperties, this.objFormsDefinition).pipe(
            tap(sortedFormDefinition => (this.objFormsDefinition = sortedFormDefinition))
          );
          console.log('this.objFormsDefinition :', this.objFormsDefinition);
        }),
        switchMap(() =>
          this._formService.addFormCtrlToObjForm(
            { frmCtrl: this._formBuilder.control(0), frmName: 'patch_update' },
            this.objForm
          ).pipe(
            concatMap(objForm => {
              if (this.obj.config['geometry_type']) {
                const validatorRequired =
                  this.obj.objectType == 'sites_group'
                    ? this._formBuilder.control('')
                    : this._formBuilder.control('', Validators.required);
                let frmCtrlGeom = {
                  frmCtrl: validatorRequired,
                  frmName: 'geometry',
                };
                return this._formService.addFormCtrlToObjForm(frmCtrlGeom, objForm);
              }
              return of(objForm);
            })
          )
        ),
        tap(objForm => {
          this.objForm = objForm;
          this.geomCalculated = this.obj.properties.hasOwnProperty('is_geom_from_child')
            ? this.obj.properties['is_geom_from_child']
            : false;
          this.geomCalculated ? (this.obj.geometry = null) : null;
          this.bEdit ? this._geojsonService.setCurrentmapData(this.obj.geometry, this.geomCalculated) : null;
        }),
        switchMap(() => this.setQueryParams(this.obj)),
        tap(obj => {
          this.obj = obj;
          console.log(
            " On match les valeurs de l'objet en lien avec l'object Form et ensuite on patch l'object form"
          );
        }),
        switchMap(obj => this.initObjFormValues(obj, this.confiGenericSpec, Array.from(this.idsTypesSite))),
        switchMap(genericFormValues =>
          defer(() => {
            if (this.isSiteObject && !this.isEditObject) {
              return this.initObjFormSpecificValues(this.obj, this.allTypesSiteConfig).pipe(defaultIfEmpty(null));
            } else if (this.isSiteObject && this.isEditObject) {
              const filteredTypesSiteConfig = Utils.filterObject(this.allTypesSiteConfig, Array.from(this.idsTypesSite));
              return this.initObjFormSpecificValues(this.obj, filteredTypesSiteConfig).pipe(defaultIfEmpty(null));
            } else {
              return of(null);
            }
          }).pipe(
            tap(specificFormValues => {
              console.log("Patching the object form values");
              this.objForm.patchValue(genericFormValues);
              if (specificFormValues !== null) {
                this._formService.patchValuesInDynamicGroups(specificFormValues, this.objFormsDynamic);
              }
            })
          )
        )
      )
      .subscribe(() => {
        console.log(' ObjForm Initialized');
        console.log(this.objForm);
        console.log(' ObjFormDynamic Initialized');
        console.log(this.objFormsDynamic);

        const dynamicGroupsArray = this.objForm.get('dynamicGroups') as FormArray;
        this.subscribeToDynamicGroupsChanges(dynamicGroupsArray);
      });
  }

  subscribeToDynamicGroupsChanges(dynamicGroupsArray: FormArray): void {
    dynamicGroupsArray.valueChanges.pipe(
      scan((prevLength, currentValue) => dynamicGroupsArray.controls.length, 0),
      distinctUntilChanged()
    ).subscribe((length) => {
      this.hasDynamicGroups = length > 0;
    });
  }
  
  /** pour réutiliser des paramètres déjà saisis */
  keepDefinitions() {
    return this.objFormsDefinition.filter((def) =>
      this.obj.configParam('keep').includes(def.attribut_name)
    );
  }

  setQueryParams(obj: MonitoringObject) {
    // par le biais des parametre query de route on donne l'id du ou des parents
    // permet d'avoir un 'tree' ou un objet est sur plusieurs branches
    // on attend des ids d'où test avec parseInt
    for (const key of Object.keys(this.queryParams)) {
      const strToInt = parseInt(this.queryParams[key]);
      if (!Number.isNaN(strToInt)) {
        obj.properties[key] = strToInt;
      }
    }
    return of(obj);
  }

  /** initialise le formulaire quand le formulaire est prêt ou l'object est prêt */
  initForm() {
    if (!(this.objForm && this.obj.bIsInitialized)) {
      return;
    }
    this._formService
      .formValues(this.obj, this.confiGenericSpec)
      .pipe(
        map((genericFormValues) => {
          genericFormValues['types_site'] = Array.from(this.idsTypesSite);
          return genericFormValues;
        })
      )
      .subscribe((formValue) => {
        this.objForm.patchValue(formValue);
        this.setDefaultFormValue();
      });
  }

  initFormDynamic(typeSite: string) {
    if (!(this.objFormsDynamic[typeSite] && this.obj.bIsInitialized)) {
      return;
    }
    if(this.isInitialzedObjFormDynamic && this.isInitialzedObjFormDynamic[typeSite]){
      this._formService
      .formValues(this.obj, this.allTypesSiteConfig[typeSite])
      .subscribe((formValue) => {
        this._formService.patchValuesInFormGroup(this.objFormsDynamic[typeSite], formValue);
        this.isInitialzedObjFormDynamic[typeSite] = false;
      });
    }
    // pour donner la valeur de l'objet au formulaire

   
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
    // if (this.obj.objectType == 'site') {
    //   this.dataComplement = { ...this.typesSiteConfig, types_site: this.idsTypesSite };
    // }
    let objFormValueGroup = {};
    this.isSiteObject
      ? (objFormValueGroup = this._formService.flattenFormGroup(this.objForm))
      : (objFormValueGroup = this.objForm.value);
    // this.obj.objectType == 'site'
    //   ? Object.assign(this.obj.config['specific'], this.schemaUpdate)
    //   : null;
    const action = this.obj.id
      ? this.obj.patch(objFormValueGroup)
      : this.obj.post(objFormValueGroup);
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
    console.log('CHANGE MAIN FORM');
    // Check si types_site est modifié
    if (event.types_site != null && event.types_site.length != this.idsTypesSite.size) {
      this.updateTypeSiteForm().subscribe((_) => {
        this.objForm = this._formService.addMultipleFormGroupsToObjForm(this.objFormsDynamic, this.objForm);
      });
    }
    const change = this.obj.change();
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objForm, meta: this.meta });
    }, 100);
  }

  onObjFormValueChangeDynamic(event, typeSite) {
    console.log('CHANGE DYNAMIC');
    this.objForm = this._formService.addMultipleFormGroupsToObjForm(this.objFormsDynamic, this.objForm);
    const change = this.obj.change();
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objFormsDynamic[typeSite], meta: this.meta });
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
              return of({ [idTypeSite]: this.allTypesSiteConfig[idTypeSite] });
            }),
            reduce((acc, cur) => ({ ...acc, ...cur }), {})
          )
        )
      ),
      filter((typesSiteObject) => {
        // Ici on filtre pour empêcher de continuer l'enchainement cascade des opérations suivant si la liste des types de site est vide
        const isTypeSelectedEmpty =
          typesSiteObject === null || Object.keys(typesSiteObject).length === 0;
        if (isTypeSelectedEmpty) {
          this.idsTypesSite = new Set<number>();
          Object.keys(this.isInitialzedObjFormDynamic).forEach((key) => this.isInitialzedObjFormDynamic[key] = true);
          this.removeAllDynamicGroups();
        }
        return !isTypeSelectedEmpty;
      }),
      tap((typesSiteObject) => {
        this.typesSiteConfig = typesSiteObject;
        this.idsTypesSite = new Set<number>(Object.keys(typesSiteObject).map(Number)); // Update idsTypesSite with the keys of filteredTypeSiteConfig
      }),
      concatMap(() => {
        const keys = Object.keys(this.typesSiteConfig);

        // Create or update form groups for each typeSite
        keys.forEach((typeSite) => {
          if (!this.objFormsDynamic[typeSite]) {
            // Si dans la liste de type de site un nouveau type de site est ajouté alors on créé un formGroup
            this.objFormsDynamic[typeSite] = this._formBuilder.group({});
            this.isInitialzedObjFormDynamic[typeSite] = true;
          }
        });

        // Si la nouvelle liste de type de site ne match pas avec la liste de "keys" du objFormDynamic on supprime
        Object.keys(this.objFormsDynamic).forEach((key) => {
          if (!keys.includes(key)) {
            this.isInitialzedObjFormDynamic[key] = true;
            delete this.objFormsDynamic[key];
          }
        });
        console.log('Initialisation objFormsDynamic avec comme keys:', keys);

        return forkJoin(
          keys.map((typeSite) => {
            return this.initObjFormDefiniton(this.typesSiteConfig[typeSite], this.meta).pipe(
              tap((objFormDefinition) => {
                console.log(
                  'Initialisation de l objFormDefinition basé sur les nouveaux types de sites',
                  typeSite,
                  objFormDefinition
                );
                this.objFormsDefinitionDynamic[typeSite] = objFormDefinition;
              })
            );
          })
        );
      })
      // TODO: VERIFIER SI NECESSAIRE (A PRIORI à l'ajout de site non mais peut être nécessaire si
      // on veut garder les valeurs qui étaient présente pour l'édition d'un site)
      // concatMap(() => {
      //   return forkJoin(
      //     Object.entries(this.typesSiteConfig).map(([typeSite, config]) => {
      //       return this.initObjFormSpecificValues(this.obj, config).pipe(
      //         map((formValue) => ({
      //           typeSite,
      //           formValue
      //         }))
      //       );
      //     })
      //   ).pipe(
      //     tap(() => console.log('All initObjFormSpecificValues completed'))
      //   );
      // }),
      // map((results) => {
      //   results.forEach(({ typeSite, formValue }) => {
      //     this.objFormsDynamic[typeSite].patchValue(formValue);
      //   });
      //   console.log('All operations completed');
      //   return results;
      // })
    );
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


  initObjFormDefiniton(schema: JsonData, meta: JsonData) {
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
    return of(objectFormDefiniton);
  }

  /**
   * Initializes some variables for the component based on the given `MonitoringObject`.
   * @param obj The `MonitoringObject` used to initialize the variables.
   * @returns An object with the initialized variables.
   */
  initializeVariables$(obj: MonitoringObject): Observable<{ isSiteObject: boolean, isEditObject: boolean, hasDynamicGroups: boolean }> {
    const isSiteObject = obj.objectType === 'site';
    const isEditObject = obj.id !== undefined && obj.id !== null;
    const hasDynamicGroups = isSiteObject && obj.properties['types_site'].length > 0;
    
    return of({ isSiteObject, isEditObject, hasDynamicGroups })
  }

  initializeTypeSiteConfig(genericConfig, specificConfig, typesSiteConfig, propertiesTypesSite): Observable<{ specificConfig: any, confiGenericSpec: any, allTypesSiteConfig: any, idsTypesSiteSet: Set<number> }> {
    return this.initTypeSiteConfig(
      specificConfig,
      propertiesTypesSite,
      typesSiteConfig
    ).pipe(
      concatMap(({ idsTypesSite, typesSiteConfig }) => {
        const allTypesSiteConfig = typesSiteConfig;
        const idsTypesSiteSet = new Set(idsTypesSite);

        const dynamicForms$ = of(null).pipe(
          concatMap(() => {
            const objFiltered = Utils.filterObject(allTypesSiteConfig, Array.from(idsTypesSiteSet));
            for (const typeSite in objFiltered) {
              this.addDynamicFormGroup(typeSite);
              this.isInitialzedObjFormDynamic[typeSite] = true;
            }
            return of(null);
          })
        );

        return dynamicForms$.pipe(
          concatMap(() => {
            return this.initializeSpecificConfig(genericConfig, specificConfig,typesSiteConfig, allTypesSiteConfig).pipe(
              concatMap(({ specificConfig, confiGenericSpec }) => {
                return of({ specificConfig, confiGenericSpec, allTypesSiteConfig, idsTypesSiteSet });
              })
            );
          })
        );
      })
    );
  }

  initializeSpecificConfig(genericConfig, specificConfig, configTyepSite = {}, allTypesSiteConfig = {}): Observable<{ specificConfig: any, confiGenericSpec: any }> {
    return this.initSpecificConfig(
      specificConfig,
      configTyepSite,
      allTypesSiteConfig
    ).pipe(
      concatMap(specificConfig => {
        const confiGenericSpec = Utils.mergeObjects(specificConfig, genericConfig);
        return of({ specificConfig, confiGenericSpec });
      })
    );
  }

  initTypeSiteConfig(configSpecific, typeSiteProperties, configTypesSite) {
    const idsTypesSite = [];
    const typesSiteConfig = {};
    for (const keyTypeSite in configTypesSite) {
      typesSiteConfig[keyTypeSite] = {};
      let typeSiteName = configTypesSite[keyTypeSite].name;
      for (const prop of configTypesSite[keyTypeSite].display_properties) {
        typesSiteConfig[keyTypeSite][prop] = configSpecific[prop];
      }
      typeSiteProperties.includes(typeSiteName)
        ? idsTypesSite.push(parseInt(keyTypeSite))
        : null;
    }
    return of({ idsTypesSite, typesSiteConfig });
  }

  initSpecificConfig(configSpecific, configTypesSite = {}, allTypesSiteConfig = {}) {
    let specificConfig = {};
    if (configTypesSite) {
      const allTypeSiteConfigCombined = Object.assign(
        {},
        ...Object.values(allTypesSiteConfig)
      );
      specificConfig = Utils.getRemainingProperties(allTypeSiteConfigCombined, configSpecific);
    } else {
      specificConfig = configSpecific;
    }
    return of(specificConfig);
  }

  sortObjFormDefinition(displayProperties: string[], objFormDef: JsonData) {
    // let displayProperties = [...(this.obj.configParam('display_properties') || [])];
    // TODO: Vérifier mais normalement plus nécessaire d'utiliser cette évaluation de condition (objFormDef ne devrait pas être nul ici)
    if (!objFormDef) return;
    if (displayProperties && displayProperties.length) {
      displayProperties.reverse();
      objFormDef.sort((a, b) => {
        let indexA = displayProperties.findIndex((e) => e == a.attribut_name);
        let indexB = displayProperties.findIndex((e) => e == b.attribut_name);
        return indexB - indexA;
      });
    }
    return of(objFormDef);
  }

  initObjFormValues(obj, config, idsTypesSite = []) {
    return this._formService.formValues(obj, config).pipe(
      concatMap((genericFormValues) => {
        if (idsTypesSite.length != 0) {
          genericFormValues['types_site'] = idsTypesSite;
        }
        return of(genericFormValues);
      })
    );
  }

  initObjFormSpecificValues(obj, config) {
    return this._formService.formValues(obj, config);
  }

  
  addDynamicFormGroup(groupName: string) {
    const newFormGroup = this._formBuilder.group({});
    this.objFormsDynamic[groupName] = newFormGroup;
    return of(newFormGroup);
  }

  removeDynamicFormGroup(groupName: string): void {
    // Remove form group from objFormsDynamic
    delete this.objFormsDynamic[groupName];
    delete this.objFormsDefinitionDynamic[groupName];

    // Remove form group from the dynamicGroups FormArray
    const dynamicGroupsArray = this.objForm.get('dynamicGroups') as FormArray;
    const index = dynamicGroupsArray.controls.findIndex(
      (group) => group === this.objFormsDynamic[groupName]
    );
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

  createFormWithDynamicGroups(objFormGroup): FormGroup {
    const dynamicGroups = this._formBuilder.array([]);
    objFormGroup.addControl('dynamicGroups', dynamicGroups);
    return objFormGroup;
  }

  // TODO: VERIFIER si on garde cette "method" pour vérifier la validité des formGroup liés aux types de sites
  // Pour l'instant on choisi de ne garder que l'objForm qui contient le formArray dynamicGroup
  // qui lui même contient l'équivalent de l'ensemble des formGroup liés aux types de site
  areDynamicFormsValid(): boolean {
    // Iterate through each objFormDynamic and check if it's valid
    for (const typeSite in this.objFormsDynamic) {
      if (this.objFormsDynamic.hasOwnProperty(typeSite)) {
        const objFormDynamic = this.objFormsDynamic[typeSite];
        if (!objFormDynamic.valid) {
          return false; // If any objFormDynamic is invalid, return false
        }
      }
    }
    return true; // If all objFormsDynamic are valid, return true
  }

  ngOnDestroy() {
    this.objForm.patchValue({ geometry: null });
  }
}
