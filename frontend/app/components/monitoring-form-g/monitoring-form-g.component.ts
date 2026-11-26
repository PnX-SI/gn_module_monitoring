import { forkJoin, Observable, of, EMPTY, Subscription } from 'rxjs';
import { concatMap, debounceTime } from 'rxjs/operators';
import { Component, OnInit, Input, AfterViewInit, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators, FormControl, FormArray } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';
import { TranslateService } from '@ngx-translate/core';
import { NgSelectConfig } from '@ng-select/ng-select';
import { evaluate } from '@marcbachmann/cel-js';

import { CommonService } from '@geonature_common/service/common.service';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';
import { Utils } from '../../utils/utils';
import { ApiService } from '../../services/api-geom.service';
import { FormService } from '../../services/form.service';
import { DataUtilsService } from '../../services/data-utils.service';
import { JsonData } from '../../types/jsondata';
import { GeoJSONService, DisplayMode } from '../../services/geojson.service';
import { NavigationService } from '../../services/navigation.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { PermissionService } from '../../services/permission.service';
import { ObjectService } from '../../services/object.service';
import { TOOLTIPMESSAGEALERT, TOOLTIPMESSAGEALERT_CHILD } from '../../constants/guard';
import { Popup } from '../../utils/popup';

@Component({
  selector: 'pnx-monitoring-form-g',
  templateUrl: './monitoring-form-g.component.html',
  styleUrls: ['./monitoring-form-g.component.css'],
  // Listes déroulantes ng-select rattachées au body pour ne pas être coupées par le scroll du formulaire
  providers: [
    {
      provide: NgSelectConfig,
      useFactory: () => Object.assign(new NgSelectConfig(), { appendTo: 'body' }),
    },
  ],
})
export class MonitoringFormGComponent implements OnInit, AfterViewInit {
  @Input() apiService: ApiService;
  @Input() object: any;
  @Input() form: FormGroup = new FormGroup('');
  @Input() config: any;
  validationError: string[] = [];
  fieldErrors: { [name: string]: string[] } = {};
  private validationSub: Subscription;
  @Input() currentUser: any;
  @Input() objectType: string;
  // Dans le cas de création, la liste des parents est fournie par le resolver du composant parent
  // Dans le cas de mise à jour, la liste des parents est fournie via l'objet
  @Input() fetchedParents: JsonData | null = null;
  @Output() EditChange = new EventEmitter<boolean>();

  public meta: any;
  public saveAndAddChildrenSpinner: boolean = false;
  public saveSpinner: boolean = false;
  public formReady: boolean = true;
  public chainInput: boolean = false;
  // Nombre d'objets validés depuis le début de la saisie enchaînée
  public chainedCount = 0;
  public canUpdate: boolean = false;
  public canDelete: boolean = false;
  public addChildren: boolean = false;
  public formsDefinition: JsonData;
  public userPermission: any;
  public toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;

  public deleteSpinner = false;
  public deleteModal = false;

  private queryParams: any;
  private pendingKeepValues: JsonData | null = null;
  private initialFormValue: JsonData | null = null;

  constructor(
    public _commonService: CommonService,
    public _formService: FormService,
    public _dataUtilsService: DataUtilsService,
    private _dynformService: DynamicFormService,
    private _formBuilder: FormBuilder,
    private _location: Location,
    private _geojsonService: GeoJSONService,
    private _navigationService: NavigationService,
    private _route: ActivatedRoute,
    private translate: TranslateService,
    protected _configServiceG: ConfigServiceG,
    private _permissionService: PermissionService,
    private _objectService: ObjectService,
    private _popup: Popup
  ) {}

  private buildParentsMeta(): JsonData {
    return this.object?.parents || this.fetchedParents || {};
  }

  ngAfterViewInit() {
    if (this.object) {
      this.form.patchValue(this.object);
    }
    this.setDefaultFormValue();

    this.publishGeometryControl();

    // Conversion asynchrone des valeurs de l'objet pour les widgets (dates, observateurs, ...) :
    // tant qu'elle n'est pas terminée, le formulaire contient les valeurs brutes de l'API,
    // que formatForApi ne sait pas relire (envoi de valeurs nulles)
    this.formValues(this.form.value).subscribe({
      next: (formValue) => {
        this.form.patchValue(formValue);
        this.initialFormValue = this.form.value;
      },
      complete: () => setTimeout(() => (this.formReady = true)),
      error: () => setTimeout(() => (this.formReady = true)),
    });

    // Affichage de la geometrie des sites et groupes de sites du module
    this.display_geometry();
  }

  initForm() {
    this.meta = {
      nomenclatures: this._dataUtilsService.getDataUtil('nomenclature') || {},
      dataset: this._dataUtilsService.getDataUtil('dataset'),
      id_role: this.currentUser.id_role,
      bChainInput: this.chainInput,
      parents: this.buildParentsMeta(),
    };
    if (this.config['geometry_type']) {
      const validatorRequired =
        this.objectType == 'sites_group'
          ? this._formBuilder.control('')
          : this._formBuilder.control('', Validators.required);

      let frmCtrlGeom = {
        frmCtrl: validatorRequired,
        frmName: 'geometry',
      };

      this.form = this._formService.addFormCtrlToObjForm(frmCtrlGeom, this.form);
      if (this.object) {
        const geomCalculated = this.object.hasOwnProperty('is_geom_from_child')
          ? this.object['is_geom_from_child']
          : false;
        if (geomCalculated) {
          this.object.geometry = null;
        } else {
          // TODO pourquoi la conversion en JSON ici ?
          this.object.geometry = this.object.geometry;
        }
      }
    }

    if (!this.object) {
      this.prefillParentFormValue();
    }

    this.setDefaultFormValue();
  }

  prefillParentFormValue() {
    const parentsPath = this.queryParams['parents_path'] || [];
    const parentType = parentsPath[parentsPath.length - 1];
    if (!parentType) {
      return;
    }

    const parentFieldId = (this._configServiceG.config()?.[parentType] || {})['id_field_name'];
    if (parentFieldId && this.queryParams[parentFieldId] != null) {
      const rawValue = this.queryParams[parentFieldId];
      const numericValue = Number(rawValue);
      this.form.patchValue({
        [parentFieldId]: Number.isNaN(numericValue) ? rawValue : numericValue,
      });
    }
  }

  initPermission() {
    this.userPermission =
      this.currentUser?.moduleCruved ||
      this._permissionService.setModulePermissions(this._configServiceG.moduleCode() || 'generic');

    const objectPermission = this.userPermission[this.objectType.toString()] || {};
    const isCreate = !this.object;
    // droits sur l'objet lui-même (scope « mes données » / « mon organisme »), calculés par l'API
    const objectCruved = this.objectType != 'module' ? this.object?.cruved : undefined;

    this.canUpdate = isCreate
      ? objectPermission['C'] > 0
      : objectCruved
        ? !!objectCruved['U']
        : objectPermission['U'] > 0;

    if (isCreate || this.objectType == 'module') {
      this.canDelete = false;
      return;
    }

    const nbChildren =
      (this.object['nb_sites'] || 0) +
      (this.object['nb_visits'] || 0) +
      (this.object['nb_observations'] || 0) +
      (this.object['nb_marking_events'] || 0);

    if (nbChildren > 0) {
      this.canDelete = false;
      this.toolTipNotAllowed = TOOLTIPMESSAGEALERT_CHILD;
    } else {
      this.canDelete = objectCruved ? !!objectCruved['D'] : objectPermission['D'] > 0;
    }
  }

  ngOnInit() {
    this.queryParams = this._route.snapshot.queryParams || {};
    this.formReady = !this.object;
    this.initForm();
    this.subscribeEntityValidation();
    this.initPermission();
    if (this.fetchedParents) {
      this.meta.parents = this.buildParentsMeta();
    }
    let displayProperties = [...(this.config.display_properties || [])];
    this.formsDefinition = this.sortFormDefinition(
      displayProperties,
      this.initFormDefiniton(this.config.fields, this.meta)
    );
  }

  setDefaultFormValue() {
    const value = this.form.value;
    const date = new Date();
    const isoDate =
      date.getFullYear() +
      '-' +
      String(date.getMonth() + 1).padStart(2, '0') +
      '-' +
      String(date.getDate()).padStart(2, '0');

    const defaultValue = {
      id_digitiser: value['id_digitiser'] || this.currentUser.id_role,
      id_inventor: value['id_inventor'] || this.currentUser.id_role,
      first_use_date: value['first_use_date'] || isoDate,
      medias: value['medias'] || [],
    };
    this.form.patchValue(defaultValue);
  }

  onFormValueChange(event) {
    const change = this.config.change;
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.form, meta: this.meta });
    }, 100);
  }

  initFormDefiniton(schema: JsonData, meta: JsonData) {
    const objectFormDefiniton = this._dynformService
      .formDefinitionsdictToArray(schema, this.meta)
      .filter((formDef) => formDef.type_widget)
      .map((formDef) => this.applyCelDefinition(formDef))
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

  notAllowedMessage() {
    this._commonService.translateToaster(
      'warning',
      "Vous n'avez pas les permissions nécessaires pour éditer l'objet"
    );
  }

  /**
   * Convertit une valeur en valeur CEL : les dates et heures deviennent des timestamps
   * (dates à minuit UTC, heures sur le 1970-01-01 UTC) pour pouvoir être comparées.
   */
  private toCelValue(value: any, typeWidget?: string): any {
    if (value === undefined || value === null) {
      return null;
    }
    if (typeWidget === 'date') {
      if (typeof value === 'object') {
        return value.year && value.month && value.day
          ? new Date(Date.UTC(value.year, value.month - 1, value.day))
          : null;
      }
      const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value));
      return match ? new Date(Date.UTC(+match[1], +match[2] - 1, +match[3])) : null;
    }
    if (typeWidget === 'time') {
      const match = /^(\d{2}):(\d{2})(?::(\d{2}))?/.exec(String(value));
      return match ? new Date(Date.UTC(1970, 0, 1, +match[1], +match[2], +(match[3] || 0))) : null;
    }
    return value;
  }

  /**
   * Parents de l’objet, accessibles par leur type (`site`, `sites_group`…) selon `parent_types`
   * de la configuration, comme `meta.parents` dans les expressions js.
   */
  private buildParentsCelContext(): JsonData {
    const parents = this.buildParentsMeta();
    const parentsConfig = this._configServiceG.config() || {};
    const context: JsonData = {};
    for (const parentType of this.config?.['parent_types'] || []) {
      const parent = parents[parentType];
      if (!parent) {
        context[parentType] = null;
        continue;
      }
      const parentFields = parentsConfig[parentType]?.['fields'] || {};
      context[parentType] = Object.fromEntries(
        Object.entries(parent).map(([key, value]) => [
          key,
          this.toCelValue(value, parentFields[key]?.['type_widget']),
        ])
      );
    }
    return context;
  }

  /**
   * Contexte CEL : les champs sont accessibles via `fields` (`fields.accessibility`),
   * les parents via leur type (`site`). Les médias ne sont pas dans le contexte.
   */
  private buildCelContext(formValue: JsonData): JsonData {
    const fieldsConfig = this.config?.['fields'] || {};
    const fields = Object.fromEntries(
      Object.entries(formValue)
        .filter(([key]) => fieldsConfig[key]?.['type_widget'] !== 'medias')
        .map(([key, value]) => [
          key,
          this.toCelValue(value, fieldsConfig[key]?.['type_widget']),
        ])
    );
    return { ...this.buildParentsCelContext(), fields };
  }

  /** Évalue une condition CEL booléenne (`hidden_cel`, `required_cel`). Faux en cas d’erreur. */
  private evaluateCelBoolean(condition: string, context: JsonData): boolean {
    try {
      return evaluate(condition, context) === true;
    } catch (e) {
      console.error(`Expression CEL impossible à évaluer : ${condition}`, e);
      return false;
    }
  }

  /**
   * `hidden_cel` et `required_cel` remplacent `hidden` et `required` : la propriété
   * devient une fonction évaluée sur la valeur du formulaire (cf. DynamicFormService.getFormDefValue),
   * ce qui met à jour l'affichage et les validateurs à chaque modification.
   */
  private applyCelDefinition(formDef: JsonData): JsonData {
    if (formDef['hidden_cel']) {
      const condition = formDef['hidden_cel'];
      formDef['hidden'] = ({ value }) =>
        this.evaluateCelBoolean(condition, this.buildCelContext(value));
    }
    if (formDef['required_cel']) {
      const condition = formDef['required_cel'];
      formDef['required'] = ({ value }) =>
        this.evaluateCelBoolean(condition, this.buildCelContext(value));
    }
    return formDef;
  }

  /**
   * Évalue toutes les conditions CEL (liste de {condition, message}) et retourne
   * les messages des conditions non respectées.
   */
  private evaluateCelConditions(conditions: any, context: JsonData): string[] {
    const errors: string[] = [];
    for (const item of conditions || []) {
      const { condition, message } =
        typeof item === 'string' ? { condition: item, message: null } : item;
      console.log('[CEL] évaluation validate_cel', condition, 'contexte', context);
      try {
        const result = evaluate(condition, context);
        console.log('[CEL] résultat validate_cel', result);
        if (typeof result !== 'boolean') {
          errors.push(`Expression de validation non booléenne : ${result}`);
        } else if (!result) {
          errors.push(message || `The following condition is not met: ${condition}`);
        }
      } catch (e) {
        errors.push(`Expression de validation impossible à évaluer : ${(e as Error).message}`);
      }
    }
    return errors;
  }

  /** Conditions `validate_cel` de l’entité, évaluées sur l’ensemble du formulaire. */
  checkEntityValidateCel(formValue: JsonData): string[] {
    return this.evaluateCelConditions(
      this.config?.['validate_cel'],
      this.buildCelContext(formValue)
    );
  }

  /**
   * Conditions `validate_cel` de chaque champ : évaluées seulement si le champ a une valeur.
   * Retourne les messages par nom de champ.
   */
  checkFieldValidateCel(formValue: JsonData): { [name: string]: string[] } {
    const context = this.buildCelContext(formValue);
    const errors: { [name: string]: string[] } = {};
    for (const [name, field] of Object.entries(this.config?.['fields'] || {})) {
      if (formValue[name] === undefined || formValue[name] === null) {
        continue;
      }
      const messages = this.evaluateCelConditions((field as JsonData)['validate_cel'], context);
      if (messages.length) {
        errors[name] = messages;
      }
    }
    return errors;
  }

  onSubmit(isAddChildrend = false) {
    if (!this.formReady) {
      return;
    }

    let formValueGroup = this.form.value;

    this.validationError = this.checkEntityValidateCel(formValueGroup);
    this.fieldErrors = this.checkFieldValidateCel(formValueGroup);
    if (this.validationError.length || Object.keys(this.fieldErrors).length) {
      return;
    }

    isAddChildrend ? (this.saveAndAddChildrenSpinner = true) : (this.saveSpinner = true);

    let actionLabel = '';
    let action;
    if (this.object && (this.object || [])[this.object.pk] !== undefined) {
      action = this.apiService.patch(
        this.object[this.object.pk],
        this.formatForApi(formValueGroup)
      );
      actionLabel = 'Modification';
    } else {
      action = this.apiService.create(this.formatForApi(formValueGroup));
      actionLabel = 'Création';
    }

    action.subscribe((objData) => {
      this.object = objData;
      this._commonService.regularToaster('success', actionLabel);
      this.saveSpinner = this.saveAndAddChildrenSpinner = false;
      /** si c'est un module : rechargement de la config puis de la page d'accueil du module
       * pour prendre en compte les modifications (ex: statut 'configured') */
      if (this.objectType === 'module') {
        const moduleCode = this.apiService._getModuleCode();
        this._formService.changeCurrentEditMode(false);
        this._configServiceG
          .loadConfig(moduleCode)
          .subscribe(() => this._navigationService.reloadModuleHome(moduleCode));
        return;
      }
      if (this.chainInput) {
        this.resetForm();
      } else if (isAddChildrend) {
        this.navigateToAddChildren();
      } else {
        if (this.config['redirect_to_parent']) {
          this.navigateToParent();
        } else {
          this.navigateToDetail();
        }
      }
    });
  }

  sortFormDefinition(displayProperties: string[], formDef: JsonData) {
    //  Tri des propriétés en fonction des displays properties
    if (displayProperties && displayProperties.length) {
      displayProperties.reverse();
      formDef.sort((a, b) => {
        let indexA = displayProperties.findIndex((e) => e == a.attribut_name);
        let indexB = displayProperties.findIndex((e) => e == b.attribut_name);
        return indexB - indexA;
      });
    }
    return formDef;
  }
  formValues(objData): Observable<any> {
    if (!objData) {
      return of(true);
    }
    let schema = this.config['fields'];
    const properties = Utils.copy(objData);
    const observables = {};

    for (const attribut_name of Object.keys(schema)) {
      const elem = schema[attribut_name];
      if (!(elem || [])['type_widget']) {
        continue;
      }
      if (!(attribut_name in properties)) {
        continue;
      }
      observables[attribut_name] = this._formService.toForm(elem, properties[attribut_name]);
    }

    return forkJoin(observables).pipe(
      concatMap((formValues_in) => {
        const formValues = Utils.copy(formValues_in);
        // geometry
        if (this.config['geometry_type'] && this.object?.geom) {
          formValues['geometry'] = this.object.geom;
        }
        return of(formValues);
      })
    );
  }

  formatForApi(formValue: any) {
    let data = {};
    let fields = this.config.fields;
    for (const attribut_name of Object.keys(fields)) {
      const elem = fields[attribut_name];
      if (!elem?.type_widget) {
        continue;
      }

      data[attribut_name] = this._formService.fromForm(elem, formValue[attribut_name]);
      // data[attribut_name] = formValue[attribut_name];
    }
    if (formValue['geometry'] !== null) {
      data['geom'] = formValue['geometry']?.geometry;
    }
    return data;
  }

  display_geometry() {
    // Affichage des
    let displayType: DisplayMode = 'info';
    if (!this.object) {
      displayType = 'info_zoom';
    }
    if (!['sites_group', 'site'].includes(this.objectType)) {
      return;
    }
    if (this.objectType == 'sites_group') {
      this._geojsonService.getSitesGroupsGeometries(this.onEachFeatureGroupSite(), {}, displayType);
    }
    if (this.objectType == 'site') {
      // Get id_sites_group
      const id_sites_group =
        (this.queryParams || [])['id_sites_group'] || (this.object || [])['id_sites_group'];

      // S'il y a un id_site group
      // et qu'il est spécifié dans les parents_path
      // Affichage
      if (
        id_sites_group &&
        ('id_sites_group' in this.queryParams ||
          (this.queryParams['parents_path'] || []).includes('sites_group'))
      ) {
        // Display sites group and sites
        this._geojsonService.getSitesGroupsGeometriesWithSites(
          this.onEachFeatureGroupSite(),
          this.onEachFeatureSite(),
          { id_sites_group: id_sites_group },
          { id_sites_group: id_sites_group },
          displayType
        );
      } else {
        // Display site
        this._geojsonService.getSitesGroupsChildGeometries(
          this.onEachFeatureSite(),
          {},
          displayType
        );
      }
    }
  }
  onEachFeatureSite() {
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(this._configServiceG.moduleCode(), feature, {
        parents_path: ['module', 'sites_group'],
      });
      layer.bindPopup(popup);
    };
  }
  onEachFeatureGroupSite() {
    return (feature, layer) => {
      const popup = this._popup.setSiteGroupPopup(this._configServiceG.moduleCode(), feature, {
        parents_path: ['module', 'sites_group'],
      });
      layer.bindPopup(popup);
    };
  }

  /**
   * Valider et renseigner les enfants
   */
  navigateToAddChildren() {
    // TODO CHANGE action=> Rafraichir les données si l'enregistrement c'est bien passé
    // notament pour la carte
    this._formService.changeCurrentEditMode(false);

    this._navigationService.navigateToAddChildren(
      this.object[this.object.pk],
      this.object['siteId'],
      this.apiService._getModuleCode(),
      this.apiService.objectObs.objectType,
      this.apiService.objectObs.childType,
      this.queryParams['parents_path']
    );
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToDetail() {
    // Si l'objet est vide, c-a-d une création on retourne vers le parent
    if (!this.object) {
      this.navigateToParent();
      return;
    }

    this._formService.changeCurrentEditMode(false);
    this._navigationService.navigateToDetail(
      this.object[this.object.pk],
      false,
      this.apiService._getModuleCode(),
      this.apiService.objectObs.objectType,
      this.queryParams['parents_path']
    );
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToParent() {
    this.EditChange.emit(false); // patch bug navigation

    const rawParentsPath = this.queryParams['parents_path'] || [];
    const parentsPath = Array.isArray(rawParentsPath) ? rawParentsPath : [rawParentsPath];

    const parentType = parentsPath[parentsPath.length - 1];
    const parentFieldId = (this._configServiceG.config()?.[parentType] || {})['id_field_name'];
    // Si l'objet est vide, c-a-d une création l'id parent est récupéré depuis les queryParams
    const parentId = this.object?.[parentFieldId] || this.queryParams[parentFieldId];
    this._navigationService.navigateToParent(
      this.apiService._getModuleCode(),
      this.apiService.objectObs.objectType,
      parentId,
      [...parentsPath]
    );
  }

  resetForm() {
    const keep = this.config['keep'] || [];
    const currentValue = this.form.value;
    const keepValues = keep.reduce((acc: JsonData, key: string) => {
      if (key in currentValue) {
        acc[key] = currentValue[key];
      }
      return acc;
    }, {});
    // Restauration des valeurs par défaut du formulaire
    this.pendingKeepValues = { ...this.initialFormValue, ...keepValues };

    this.object = null;

    // Les contrôles sont conservés lors du changement de définition (`preserveControls`) :
    // on vide donc explicitement toutes les valeurs (géométrie incluse) avant de restaurer
    // celles à conserver dans `onDynamicFormGroupChange`
    this.form.reset();

    this.resetDynamicForm();
    // Force le rafraichissement des géométries de façon à ammender le layer avec la dernière données saisie
    this.display_geometry();
  }

  resetDynamicForm() {
    this.formsDefinition = (this.formsDefinition as any[]).map((formDef) => ({ ...formDef }));
  }

  /** Relie le composant de dessin au contrôle `geometry` courant du formulaire */
  private publishGeometryControl() {
    if (this.config['geometry_type']) {
      this._formService.changeFormMapObj({
        frmGp: this.form.controls['geometry'] as FormControl,
        geometry_type: this.config['geometry_type'],
      });
    }
  }

  onDynamicFormGroupChange() {
    this.initForm();
    if (this.pendingKeepValues) {
      this.form.patchValue(this.pendingKeepValues);
      this.pendingKeepValues = null;
    }
    this.form.updateValueAndValidity();
  }

  onCancelEdit() {
    // TODO Vérifier ce qui se passe quand annulation d'une création
    if (this.object) {
      this.object.geometry == null
        ? this._geojsonService.setMapDataWithFeatureGroup([this._geojsonService.sitesFeatureGroup])
        : this._geojsonService.setMapBeforeEdit(this.object.geometry);
    }
    this.navigateToDetail();
  }

  /**
   * Arrête la saisie enchaînée : quitte le formulaire de création (les objets déjà
   * validés sont conservés) pour retourner vers l'objet parent
   */
  onStopChain() {
    this.chainInput = false;
    this.navigateToDetail();
  }

  /**
   * Évalue les conditions `validate_cel` (entité et champs) à chaque modification du formulaire.
   * Différé de 300 ms : évite d’évaluer à chaque frappe au clavier.
   */
  private subscribeEntityValidation() {
    this.validationSub = this.form.valueChanges
      .pipe(debounceTime(300))
      .subscribe((value) => {
        this.validationError = this.checkEntityValidateCel(value);
        this.fieldErrors = this.checkFieldValidateCel(value);
        this.logHiddenRequiredEmptyFields(value);
      });
  }

  /** Définitions de tous les champs du formulaire, avec `hidden` et `required` évaluables. */
  protected fieldDefinitions(): JsonData[] {
    return this.formsDefinition as JsonData[];
  }

  /**
   * Avertit dans la console des champs masqués et requis mais vides : leur validateur reste actif
   * alors que l’utilisateur ne peut pas les renseigner.
   */
  private logHiddenRequiredEmptyFields(formValue: JsonData) {
    for (const formDef of this.fieldDefinitions()) {
      const name = formDef['attribut_name'];
      const hidden = this._dynformService.getFormDefValue(formDef, 'hidden', formValue);
      const required = this._dynformService.getFormDefValue(formDef, 'required', formValue);
      const value = formValue[name];
      const empty = value == null || value === '' || (Array.isArray(value) && !value.length);
      if (hidden && required && empty) {
        console.log(`[WARNING] Le champ '${name}' est masqué et requis, mais il est vide.`);
      }
    }
  }

  onDelete() {
    this.deleteSpinner = true;
    this.apiService.delete(this.object[this.object.pk]).subscribe((objData) => {
      this.deleteSpinner = this.deleteModal = false;

      this.object.deleted = true;
      this._formService.changeCurrentEditMode(false);
      this._commonService.regularToaster(
        'info',
        this.translate.instant('Monitoring.Actions.Deleted')
      );
      setTimeout(() => {
        this.navigateToParent();
      }, 100);
    });
  }

  ngOnDestroy() {
    this.validationSub?.unsubscribe();
    this._geojsonService.removeAllFeatureGroup();
    this.form.patchValue({ geometry: null });
    this._formService.changeFormMapObj({
      frmGp: null,
      geometry_type: null,
    });
  }
}
