import { forkJoin, Observable, of, EMPTY } from 'rxjs';
import { concatMap, switchMap } from 'rxjs/operators';
import { Component, OnInit, Input, AfterViewInit, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators, FormControl, FormArray } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';
import { TranslateService } from '@ngx-translate/core';

import { CommonService } from '@geonature_common/service/common.service';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';
import { Utils } from '../../utils/utils';
import { ApiService } from '../../services/api-geom.service';
import { FormService } from '../../services/form.service';
import { DataUtilsService } from '../../services/data-utils.service';
import { JsonData } from '../../types/jsondata';
import { GeoJSONService } from '../../services/geojson.service';
import { NavigationService } from '../../services/navigation.service';
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { PermissionService } from '../../services/permission.service';
import { ObjectService } from '../../services/object.service';
import { TOOLTIPMESSAGEALERT, TOOLTIPMESSAGEALERT_CHILD } from '../../constants/guard';

@Component({
  selector: 'pnx-monitoring-form-g',
  templateUrl: './monitoring-form-g.component.html',
  styleUrls: ['./monitoring-form-g.component.css'],
})
export class MonitoringFormGComponent implements OnInit, AfterViewInit {
  @Input() apiService: ApiService;
  @Input() object: any;
  @Input() form: FormGroup = new FormGroup('');
  @Input() config: any;
  @Input() currentUser: any;
  @Input() objectType: string;
  @Output() EditChange = new EventEmitter<boolean>();

  public meta: any;
  public saveAndAddChildrenSpinner: boolean = false;
  public saveSpinner: boolean = false;
  public chainInput: boolean = false;
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
  private fetchedParents: JsonData | null = null;

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
    private _formUtils: MonitoringObjectService,
    private translate: TranslateService,
    private _configServiceG: ConfigServiceG,
    private _permissionService: PermissionService,
    private _objectService: ObjectService
  ) {}

  private buildParentsMeta(): JsonData {
    return this.object?.parents || this.fetchedParents || {};
  }

  private loadParentsForCreation(): Observable<any> {
    // Si c'est une nouvelle entité, on récupère les parents
    // pour pouvoir les utiliser dans l'objet meta du formulaire
    // Si c'est une modification, les parents sont récupérés via le détail de l'objet

    // Identification si c'est ou non une nouvelle entité
    // Test si la clé primaire est renseignée
    const idFieldName = this.config['id_field_name'];
    if (this.object?.[idFieldName] !== undefined) {
      return EMPTY;
    }

    // Récupération de la liste des parents
    const rawParentsPath = this.queryParams['parents_path'] || [];
    const parentsPath = Array.isArray(rawParentsPath) ? rawParentsPath : [rawParentsPath];
    const parentType = parentsPath[parentsPath.length - 1];
    if (!parentType || parentType === 'module') {
      return EMPTY;
    }

    // Récupération des objets parents
    const parentService = this._objectService.getService(parentType);
    const parentFieldId = (this._configServiceG.config()?.[parentType] || {})['id_field_name'];
    const rawParentId = parentFieldId ? this.queryParams[parentFieldId] : null;
    const parentId = Number(rawParentId);
    if (!parentService || !parentFieldId || rawParentId == null || Number.isNaN(parentId)) {
      return EMPTY;
    }

    return parentService.getById(parentId, this.apiService._getModuleCode()).pipe(
      switchMap((parent: any) => {
        if (!parent) {
          return EMPTY;
        }
        const { parents: ancestors, ...parentProperties } = parent;
        this.fetchedParents = { ...(ancestors || {}), [parentType]: parentProperties };
        this.meta.parents = this.buildParentsMeta();
        return of(parent);
      })
    );
  }

  ngAfterViewInit() {
    if (this.object) {
      this.form.patchValue(this.object);
    }
    this.setDefaultFormValue();

    if (this.config['geometry_type']) {
      this._formService.changeFormMapObj({
        frmGp: this.form.controls['geometry'] as FormControl,
        geometry_type: this.config['geometry_type'],
      });
    }

    this.formValues(this.form.value).subscribe((formValue) => {
      this.form.patchValue(formValue);
    });
  }

  initForm() {
    this.meta = {
      nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
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

    this.canUpdate = isCreate ? objectPermission['C'] > 0 : objectPermission['U'] > 0;

    if (isCreate || this.objectType == 'module') {
      this.canDelete = false;
      return;
    }

    const nbChildren =
      (this.object['nb_sites'] || 0) +
      (this.object['nb_visits'] || 0) +
      (this.object['nb_observations'] || 0);

    if (nbChildren > 0) {
      this.canDelete = false;
      this.toolTipNotAllowed = TOOLTIPMESSAGEALERT_CHILD;
    } else {
      this.canDelete = objectPermission['D'] > 0;
    }
  }

  ngOnInit() {
    this.queryParams = this._route.snapshot.queryParams || {};

    // Initialisation des parents en amont de l'initialisation du formulaire
    //  car des meta.parents peuvent se trouver dans des propriétés des fields
    //    ainsi que dans la fonction change
    this.loadParentsForCreation().subscribe(() => {
      this.initForm();
      this.initPermission();

      let displayProperties = [...(this.config.display_properties || [])];
      this.formsDefinition = this.sortFormDefinition(
        displayProperties,
        this.initFormDefiniton(this.config.fields, this.meta)
      );
    });
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

  onSubmit(isAddChildrend = false) {
    isAddChildrend ? (this.saveAndAddChildrenSpinner = true) : (this.saveSpinner = true);

    let formValueGroup = this.form.value;

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
      /** si c'est un module : reset de la config */
      // if (this.obj.objectType === 'module') {
      //     this._configService.loadConfig(this.obj.moduleCode).subscribe();
      // }
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
      observables[attribut_name] = this._formUtils.toForm(elem, properties[attribut_name]);
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

      data[attribut_name] = this._formUtils.fromForm(elem, formValue[attribut_name]);
      // data[attribut_name] = formValue[attribut_name];
    }
    if (formValue['geometry'] !== null) {
      data['geom'] = formValue['geometry']?.geometry;
    }
    return data;
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
    // TODO CHANGE action=> Rafraichir les données si l'enregistrement c'est bien passé
    // notament pour la carte
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

    this._navigationService.navigateToParent(
      this.apiService._getModuleCode(),
      this.apiService.objectObs.objectType,
      this.object?.[parentFieldId],
      [...parentsPath]
    );
  }

  resetForm() {
    const keep = this.config['keep'] || [];
    const currentValue = this.form.value;
    this.pendingKeepValues = keep.reduce((acc: JsonData, key: string) => {
      if (key in currentValue) {
        acc[key] = currentValue[key];
      }
      return acc;
    }, {});

    this.object = null;

    this.form.patchValue({ geometry: null });
    this.resetDynamicForm();
  }

  resetDynamicForm() {
    this.formsDefinition = (this.formsDefinition as any[]).map((formDef) => ({ ...formDef }));
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

  onDelete() {
    this.deleteSpinner = true;
    this.apiService.delete(this.object[this.object.pk]).subscribe((objData) => {
      this.deleteSpinner = this.deleteModal = false;
      this.object.deleted = true;
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
    this.form.patchValue({ geometry: null });
    this._formService.changeFormMapObj({
      frmGp: null,
      geometry_type: null,
    });
  }
}
