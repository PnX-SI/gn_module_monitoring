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
import { TranslateService } from '@ngx-translate/core';
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

import { Location } from '@angular/common';
import { FormService } from '../../services/form.service';
import { Router } from '@angular/router';
import { TOOLTIPMESSAGEALERT, TOOLTIPMESSAGEALERT_CHILD } from '../../constants/guard';
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

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() sites: {};

  // Possibilité d'ajouter des enfants depuis le formulaire parent
  @Input() addChildren: boolean = true;

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
  isInitialzedObjFormDynamic: { keys: string; value: boolean } | {} = {};
  remainingTypeSiteProp: JsonData = {};

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
    private _geojsonService: GeoJSONService,
    private _location: Location,
    private translate: TranslateService
  ) {}

  ngOnInit() {
    // Initialisation de la variable bChainInput à false
    this._configService.setFrontendParams('bChainInput', this.bChainInput);

    // Initialisation des variables
    this.initializeVariables(this.obj);

    // Initialisation des permissions de l'utilisateur courant
    this.initPermission();

    // Récupération de la configuration du module
    this._configService
      .init(this.obj.moduleCode)
      .pipe(
        mergeMap(() => {
          return this._dataUtilsService.initModuleNomenclatures(this.obj.moduleCode);
        }),
        tap(() => {
          // Initialisation des configurations
          //  Selon si l'objet est ou non de type site
          if (this.isSiteObject) {
            this.initializeTypeSiteConfig(
              this.obj.config['generic'],
              this.obj.config['specific'],
              this.obj.config['types_site'],
              this.obj['properties']['types_site']
            );
            // Filtre des types de site du module par rapport au type de site de l'objet
            // Utile pour afficher les formulaires des types de sites de l'objet
            // Utile pour traiter les types de site de l'objet non présents dans le module @TODO
            const objFiltered = Utils.filterObject(
              this.allTypesSiteConfig,
              Array.from(this.idsTypesSite)
            );
            this.typesSiteConfig = {};
            for (const typeSite in objFiltered) {
              this.objFormsDynamic[typeSite] = this._formBuilder.group({});
              this.isInitialzedObjFormDynamic[typeSite] = true;
              this.typesSiteConfig[typeSite] = this.allTypesSiteConfig[typeSite];
            }
            // Initialisation des sous forms group par type de site
            this._formService.addMultipleFormGroupsToObjForm(this.objFormsDynamic, this.objForm);
          } else {
            this.initializeSpecificConfig(this.obj.config['generic'], this.obj.config['specific']);
          }

          // Initialisation des paramètres par défaut du formulaire
          this.queryParams = this._route.snapshot.queryParams || {};

          this.bChainInput = this._configService.frontendParams()['bChainInput'];

          this.meta = {
            nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
            dataset: this._dataUtilsService.getDataUtil('dataset'),
            id_role: this.currentUser.id_role,
            bChainInput: this.bChainInput,
            parents: this.obj.parents,
          };

          // Récupération de la définition du formulaire
          this.objFormsDefinition = this.initObjFormDefiniton(this.confiGenericSpec, this.meta);
          // Tri des proprités en fonction de la variable display_properties
          this.displayProperties = [...(this.obj.configParam('display_properties') || [])];
          this.objFormsDefinition = this.sortObjFormDefinition(
            this.displayProperties,
            this.objFormsDefinition
          );

          // Si le type d'objet est un site rajout des définitions des types de site
          //  a l'objet principal
          if (this.isSiteObject) {
            Object.entries(this.allTypesSiteConfig).forEach(([typeSite, config]) => {
              let objFormDefinitonTypeSite = this.initObjFormDefiniton(config, this.meta);
              // Tri des propriétés spécifiques au type de site
              this.objFormsDefinitionDynamic[typeSite] = this.sortObjFormDefinition(
                this.obj.config['types_site'][typeSite]['display_properties'],
                objFormDefinitonTypeSite
              );
            });
          }
          // Ajout de controle (champ) au formulaire
          // Ajout patch_update ?? TODO comprendre pourquoi
          this.objForm = this._formService.addFormCtrlToObjForm(
            { frmCtrl: this._formBuilder.control(0), frmName: 'patch_update' },
            this.objForm
          );

          if (this.obj.config['geometry_type']) {
            const validatorRequired =
              this.obj.objectType == 'sites_group'
                ? this._formBuilder.control('')
                : this._formBuilder.control('', Validators.required);

            let frmCtrlGeom = {
              frmCtrl: validatorRequired,
              frmName: 'geometry',
            };

            this.objForm = this._formService.addFormCtrlToObjForm(frmCtrlGeom, this.objForm);
          }
          // Conversion des query params de type entier mais en string en int
          //  ??? A comprendre
          this.obj = this.setQueryParams(this.obj);
        }),
        switchMap(() =>
          this.initObjFormValues(this.obj, this.confiGenericSpec, Array.from(this.idsTypesSite))
        ),
        switchMap((genericFormValues) =>
          defer(() => {
            console.log('genericFormValues: ', genericFormValues);
            // Patch les valeurs du formulaire avec celle des propriétés spécifique aux types de site
            if (this.isSiteObject) {
              let siteConfig = this.allTypesSiteConfig;
              if (this.isEditObject) {
                siteConfig = Utils.filterObject(
                  this.allTypesSiteConfig,
                  Array.from(this.idsTypesSite)
                );
              }
              return this.initObjFormSpecificValues(this.obj, siteConfig).pipe(
                defaultIfEmpty(null)
              );
            } else {
              return of(null);
            }
          }).pipe(
            tap((specificFormValues) => {
              console.log('Patching the object form values');
              this.objForm.patchValue(genericFormValues);
              if (specificFormValues !== null) {
                this._formService.patchValuesInDynamicGroups(
                  specificFormValues,
                  this.objFormsDynamic
                );
              }
            })
          )
        )
      )
      .subscribe(() => {
        this.obj.bIsInitialized = true;
        const dynamicGroupsArray = this.objForm.get('dynamicGroups') as FormArray;
        if (dynamicGroupsArray) this.subscribeToDynamicGroupsChanges(dynamicGroupsArray);
        this.setDefaultFormValue();
        console.log('this.objFormsDefinition: ', this.objFormsDefinition);
      });
  }

  subscribeToDynamicGroupsChanges(dynamicGroupsArray: FormArray): void {
    dynamicGroupsArray.valueChanges
      .pipe(
        scan((prevLength, currentValue) => dynamicGroupsArray.controls.length, 0),
        distinctUntilChanged()
      )
      .subscribe((length) => {
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
    // par le biais des parametres query de route on donne l'id du ou des parents
    // permet d'avoir un 'tree' ou un objet est sur plusieurs branches
    // on attend des ids d'où test avec parseInt

    // TODO COMPRENDRE Comment c'est utilisé par la suite
    for (const key of Object.keys(this.queryParams)) {
      const strToInt = parseInt(this.queryParams[key]);
      if (!Number.isNaN(strToInt)) {
        obj.properties[key] = strToInt;
      }
    }
    return obj;
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
          // FIXME: renvoyer les ids des types de site coté backend et non les types de site en chaine de caractères
          if (
            this.idsTypesSite.size != 0 &&
            genericFormValues['types_site'].every(
              (item) => typeof item !== 'number' && !Number.isInteger(item)
            )
          ) {
            genericFormValues['types_site'] = Array.from(this.idsTypesSite);
          }
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
    if (this.isInitialzedObjFormDynamic && this.isInitialzedObjFormDynamic[typeSite]) {
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
    this.obj = this.setQueryParams(this.obj);

    this.obj.properties[this.obj.configParam('id_field_Name')] = null;

    // pq get ?????
    // this.obj.get(0).subscribe(() => {
    this.obj.bIsInitialized = true;
    for (const key of this.keepNames()) {
      this.obj.properties[key] = keep[key];
    }
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
    return `${action}${this.translate.instant('Monitoring.Actions.Done')}`.trim();
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
    console.log('objFormValueGroup1 : ', objFormValueGroup);
    this.isSiteObject
      ? (objFormValueGroup = this._formService.flattenFormGroup(this.objForm))
      : (objFormValueGroup = this.objForm.value);
    console.log('objFormValueGroup2 : ', objFormValueGroup);
    // this.obj.objectType == 'site'
    //   ? Object.assign(this.obj.config['specific'], this.schemaUpdate)
    //   : null;

    // On merge l'objet avec les nouvelles valeurs issues du formulaire et les propriétés mises de cotés mais qui doivent être conservées
    const finalObject = Utils.mergeObjects(this.remainingTypeSiteProp, objFormValueGroup);
    console.log('finalObject : ', finalObject);
    this.isSiteObject ? (finalObject['types_site'] = Array.from(this.idsTypesSite)) : null;
    const action = this.obj.id ? this.obj.patch(finalObject) : this.obj.post(finalObject);
    const actionLabel = this.obj.id ? 'Modification' : 'Création';
    action.subscribe((objData) => {
      this._commonService.regularToaster('success', this.msgToaster(actionLabel));
      this.bSaveSpinner = this.bSaveAndAddChildrenSpinner = false;
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
    this.bEditChange.emit(false);
    this._location.back();
    if (this.obj.id) {
      this.obj.geometry == null
        ? this._geojsonService.setMapDataWithFeatureGroup([this._geojsonService.sitesFeatureGroup])
        : this._geojsonService.setMapBeforeEdit(this.obj.geometry);
    }
  }

  onDelete() {
    this.bDeleteSpinner = true;
    this.obj.delete().subscribe((objData) => {
      this.bDeleteSpinner = this.bDeleteModal = false;
      this.obj.deleted = true;
      this._commonService.regularToaster(
        'info',
        this.msgToaster(this.translate.instant('Monitoring.Actions.Deleted'))
      );
      setTimeout(() => {
        this.navigateToParent();
      }, 100);
    });
  }

  onObjFormValueChange(event) {
    // Check si types_site est modifié
    if (event.types_site != null && event.types_site.length != this.idsTypesSite.size) {
      this.updateTypeSiteForm();
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
    this.objForm = this._formService.addMultipleFormGroupsToObjForm(
      this.objFormsDynamic,
      this.objForm
    );
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
    this.objForm.controls['types_site'].valueChanges
      .pipe(distinctUntilChanged())
      .subscribe((idsTypeSite) => {
        if (idsTypeSite && idsTypeSite.length == 0) {
          // suppresson de tous les champs dynamiques si le champs est vide
          this.removeAllDynamicGroups();
        } else {
          // // Suppressin des formGroup des idSite déselectionnés
          Object.keys(this.objFormsDynamic).forEach((key) => {
            if (!idsTypeSite.includes(parseInt(key))) {
              this.isInitialzedObjFormDynamic[key] = true;
              delete this.objFormsDynamic[key];
            }
          });
          this.idsTypesSite = new Set<number>(idsTypeSite);
          this.typesSiteConfig = {};
          // creation des nouveaux formGroup
          idsTypeSite.forEach((idTypeSite) => {
            this.typesSiteConfig[idTypeSite] = this.allTypesSiteConfig[idTypeSite];
            if (!this.objFormsDynamic[idTypeSite]) {
              // Si dans la liste de type de site un nouveau type de site est ajouté alors on créé un formGroup
              this.objFormsDynamic[idTypeSite] = this._formBuilder.group({});
              const objFormDefinition = this.initObjFormDefiniton(
                this.typesSiteConfig[idTypeSite],
                this.meta
              );
              this.objFormsDefinitionDynamic[idTypeSite] = objFormDefinition;
              this.isInitialzedObjFormDynamic[idTypeSite] = true;
            }
          });
        }
        this.objForm = this._formService.addMultipleFormGroupsToObjForm(
          this.objFormsDynamic,
          this.objForm
        );

        const change = this.obj.change();
        if (!change) {
          return;
        }

        setTimeout(() => {
          change({ objForm: this.objForm, meta: this.meta });
        }, 100);
      });
  }

  initPermission() {
    // Si les permissions n'ont pas été initialisées
    if (this.currentUser.moduleCruved == undefined) {
      this.currentUser.moduleCruved = this._configService.moduleCruved(this.obj.moduleCode);
    }

    // Calcul du nombre d'enfants pour limiter l'action de suppression
    const nb_childrens =
      this.obj.properties['nb_sites'] ||
      0 + this.obj.properties['nb_visits'] ||
      0 + this.obj.properties['nb_observations'] ||
      0;
    if (this.obj.objectType == 'module') {
      this.canDelete = false; // On ne peut pas supprimer un module
    } else if (this.obj.cruved['D'] && nb_childrens > 0) {
      this.canDelete = false; // On ne peut pas supprimer un objet s'il a des enfants
      this.toolTipNotAllowed = TOOLTIPMESSAGEALERT_CHILD;
    } else {
      this.canDelete = this.obj.cruved['D'];
    }

    // Si objet de type module ou création d'un nouvel objet
    //    => récupération des droits au niveau de la config globale et pas de l'objet
    if (this.obj.objectType == 'module') {
      this.canUpdate = this.currentUser?.moduleCruved[this.obj.objectType]['U'] > 0;
    } else if (!this.isEditObject) {
      this.canUpdate = this.currentUser?.moduleCruved[this.obj.objectType]['C'] > 0;
    } else {
      this.canUpdate = this.obj.cruved['U'];
    }
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
        if (a.attribut_name === 'medias') return 1;
        if (b.attribut_name === 'medias') return -1;
        return 0;
      })
      .sort((a, b) => {
        if (a.attribut_name === 'types_site') return 1;
        if (b.attribut_name === 'types_site') return -1;
        return 0;
      });
    return objectFormDefiniton;
  }

  /**
   * Initializes some variables for the component based on the given `MonitoringObject`.
   * @param obj The `MonitoringObject` used to initialize the variables.
   * @returns An object with the initialized variables.
   */
  initializeVariables(obj: MonitoringObject) {
    this.isSiteObject = obj.objectType === 'site';
    // Objet en édition ou création
    this.isEditObject = this.obj.id ? true : false;
    this.hasDynamicGroups = this.isSiteObject && obj.properties['types_site'].length > 0;

    this.geomCalculated = this.obj.properties.hasOwnProperty('is_geom_from_child')
      ? this.obj.properties['is_geom_from_child']
      : false;

    if (this.geomCalculated) {
      this.obj.geometry = null;
    }
    // Si mode édition initialisation du layer de l'objet en cours du composant carto
    if (this.bEdit) {
      this._geojsonService.setCurrentmapData(this.obj.geometry, this.geomCalculated);
    }
  }

  /**
   * Initializes type site config from generic config and specific config objects.
   * @param genericConfig Generic config object
   * @param specificConfig Specific config object
   * @param typesSiteConfig Type site config object
   * @param propertiesTypesSite Properties types site object
   * @returns Observable of specific config object, generic config, type site config and set of ids of type site objects
   */
  initializeTypeSiteConfig(
    genericConfig: JsonData,
    specificConfigInit: JsonData,
    typesSiteConfigInit: JsonData,
    propertiesTypesSite: any
  ) {
    const initTypeSiteConfigData = this.initTypeSiteConfig(
      specificConfigInit,
      propertiesTypesSite,
      typesSiteConfigInit
    );
    const { idsTypesSite, typesSiteConfig } = initTypeSiteConfigData;
    const allTypesSiteConfig = typesSiteConfig;
    const idsTypesSiteSet = new Set(idsTypesSite);
    this.initializeSpecificConfig(
      genericConfig,
      specificConfigInit,
      typesSiteConfig,
      allTypesSiteConfig
    );
    this.allTypesSiteConfig = allTypesSiteConfig;
    this.idsTypesSite = idsTypesSiteSet;
    // On met de coté l'ensemble des propriétés restantes et notamment (les champs "additional_data_keys" et "ids_types_site")
    const mergeConfig = Utils.mergeObjects(specificConfigInit, genericConfig);
    this.remainingTypeSiteProp = Utils.getRemainingKeys(this.obj.properties, mergeConfig);
  }

  /**
   * Initializes specific config from generic config and type site configs.
   * @param genericConfig Generic config object
   * @param specificConfig Specific config object
   * @param configTypeSite Type site config object
   * @param allTypesSiteConfig All type site config object
   */

  initializeSpecificConfig(
    genericConfig: JsonData,
    specificConfig: JsonData,
    configTypeSite: JsonData = {},
    allTypesSiteConfig: JsonData = {}
  ) {
    const cleanSpecificConfig = this.initSpecificConfig(
      specificConfig,
      configTypeSite,
      allTypesSiteConfig
    );
    const confiGenericSpec = Utils.mergeObjects(cleanSpecificConfig, genericConfig);
    this.specificConfig = specificConfig;
    this.confiGenericSpec = confiGenericSpec;
  }

  /**
   * Initializes type site config from generic config and type site properties.
   * @param configSpecific Generic config object
   * @param typeSiteProperties Type site property names array
   * @param configTypesSite Type site config object
   * @returns Observable of type site config object
   */
  initTypeSiteConfig(
    configSpecific: JsonData,
    typeSiteProperties: string[],
    configTypesSite: { [typeSiteId: string]: { display_properties: string[]; name: string } }
  ): { idsTypesSite: number[]; typesSiteConfig: { [typeSiteId: string]: JsonData } } {
    const idsTypesSite = [];
    const typesSiteConfig: { [typeSiteId: string]: JsonData } = {};
    for (const keyTypeSite in configTypesSite) {
      typesSiteConfig[keyTypeSite] = {};
      let typeSiteName = configTypesSite[keyTypeSite].name;
      for (const prop of configTypesSite[keyTypeSite].display_properties) {
        typesSiteConfig[keyTypeSite][prop] = configSpecific[prop];
      }
      typeSiteProperties.includes(typeSiteName) ? idsTypesSite.push(parseInt(keyTypeSite)) : null;
    }
    return { idsTypesSite: idsTypesSite, typesSiteConfig: typesSiteConfig };
  }

  /**
   * Initializes specific config from generic config and type site config, if any.
   * @param configSpecific Generic config object
   * @param configTypesSite Optional type site config object
   * @param allTypesSiteConfig Optional type site config object containing all type sites
   * @returns Observable of strongly typed specific config object
   */
  initSpecificConfig(
    configSpecific: JsonData,
    configTypesSite: JsonData = {},
    allTypesSiteConfig: Record<string, JsonData> = {}
  ) {
    let specificConfig: JsonData = {};
    if (Object.keys(configTypesSite).length) {
      const allTypeSiteConfigCombined = Object.assign({}, ...Object.values(allTypesSiteConfig));
      specificConfig = Utils.getRemainingProperties(allTypeSiteConfigCombined, configSpecific);
    } else {
      specificConfig = configSpecific;
    }
    return specificConfig;
  }

  sortObjFormDefinition(displayProperties: string[], objFormDef: JsonData) {
    //  Tri des propriétés en fonction des displays properties

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
    return objFormDef;
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
