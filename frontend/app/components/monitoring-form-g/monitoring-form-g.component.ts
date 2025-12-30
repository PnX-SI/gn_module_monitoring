import { Component, OnInit, Input, AfterViewInit, Output, EventEmitter } from '@angular/core';
import { ApiService } from '../../services/api-geom.service';
import { FormGroup, FormBuilder, Validators, FormControl, FormArray } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { CommonService } from '@geonature_common/service/common.service';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';
import { Location } from '@angular/common';
import { FormService } from '../../services/form.service';
import { DataUtilsService } from '../../services/data-utils.service';
import { JsonData } from '../../types/jsondata';
import { GeoJSONService } from '../../services/geojson.service';
import { NavigationService } from '../../services/navigation.service';

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
  @Input() objectType: String;
  @Output() EditChange = new EventEmitter<boolean>();

  public meta: any;
  public saveAndAddChildrenSpinner: boolean = false;
  public saveSpinner: boolean = false;
  public chainInput: boolean = false;
  public canUpdate: boolean = true;
  public canDelete: boolean = true;
  public addChildren: boolean = false;
  public formsDefinition: JsonData;
  private queryParams: {};

  constructor(
    public _commonService: CommonService,
    public _formService: FormService,
    public _dataUtilsService: DataUtilsService,
    private _dynformService: DynamicFormService,
    private _formBuilder: FormBuilder,
    private _location: Location,
    private _geojsonService: GeoJSONService,
    private _navigationService: NavigationService,
    private _route: ActivatedRoute
  ) {}

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
  }

  ngOnInit() {
    // Initialisation des variables
    // this.initializeVariables(this.obj);

    // Initialisation des permissions de l'utilisateur courant
    // this.initPermission();

    // // Initialisation des paramètres par défaut du formulaire
    this.queryParams = this._route.snapshot.queryParams || {};

    this.meta = {
      nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
      dataset: this._dataUtilsService.getDataUtil('dataset'),
      id_role: this.currentUser.id_role,
      bChainInput: this.chainInput,
      // parents: this.object.parents
    };

    // Récupération de la définition du formulaire
    this.formsDefinition = this.initFormDefiniton(this.config.fields, this.meta);
    // Tri des proprités en fonction de la variable display_properties
    let displayProperties = [...(this.config.display_properties || [])];
    this.formsDefinition = this.sortFormDefinition(displayProperties, this.formsDefinition);

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
          this.object.geometry = JSON.parse(this.object.geometry);
        }
      }
    }

    // // Conversion des query params de type entier mais en string en int
    // //  ??? A comprendre
    // this.obj = this.setQueryParams(this.obj);

  }

  setDefaultFormValue() {
    console.log('this.form before setDefaultFormValue: ', this.form);
    const value = this.form.value;
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
    this.form.patchValue(defaultValue);
    console.log('this.form after setDefaultFormValue: ', this.form);
    }


  onFormValueChange(event) {
    // const change = this.obj.change();
    // if (!change) {
    //   return;
    // }
    // setTimeout(() => {
    //   change({ objForm: this.form, meta: this.meta });
    // }, 100);
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

  initForm() {}

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
    if (this.object) {
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
        console.log('this.resetObjForm()');
        // this.resetObjForm();
      } else if (isAddChildrend) {
        console.log('this.navigateToAddChildren()');
        this.navigateToAddChildren();
      } else {
        if (this.config['redirect_to_parent']) {
          console.log('this.navigateToParent()');
          this.navigateToParent();
        } else {
          console.log('this.navigateToDetail() else');
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

  formatForApi(formValue: any) {
    let data = {};
    let fields = this.config.fields;
    for (const attribut_name of Object.keys(fields)) {
      const elem = fields[attribut_name];
      if (!elem.type_widget) {
        continue;
      }
      data[attribut_name] = formValue[attribut_name];
    }
    data['geometry'] = formValue['geometry'].geometry;
    return data;
  }

  /**
   * Valider et renseigner les enfants
   */
  navigateToAddChildren() {
    // TODO CHANGE action=> Rafraichir les données si l'enregistrement c'est bien passé
    // notament pour la carte
    // this.EditChange.emit(false); // patch bug navigation
    this._formService.changeCurrentEditMode(false);

    this._navigationService.navigateToAddChildren(
      this.object[this.object.pk],
      this.object['siteId'],
      this.apiService.objectObs.moduleCode,
      this.apiService.objectObs.objectType,
      this.apiService.objectObs.childType,
      this.queryParams['parents_path']
    );
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToDetail() {
    console.log('Form - G this.navigateToDetail()');
    console.log('queryParams:', this.queryParams);
    // TODO CHANGE action=> Rafraichir les données si l'enregistrement c'est bien passé
    // notament pour la carte
    // this.EditChange.emit(false); // patch bug navigation
    this._formService.changeCurrentEditMode(false);

    this._navigationService.navigateToDetail(
      this.object[this.object.pk],
      false,
      this.apiService.objectObs.moduleCode,
      this.apiService.objectObs.objectType,
      this.queryParams['parents_path']
    );
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToParent() {
    this.EditChange.emit(false); // patch bug navigation
    // this.object.navigateToParent();
    const parentType = (this.queryParams['parents_path'] || []).pop();
    const parentFieldId = (this.config[parentType] || [])['id_field_name'];

    this._navigationService.navigateToParent(
      this.apiService.objectObs.moduleCode,
      this.apiService.objectObs.objectType,
      this.object[parentFieldId],
      this.queryParams['parents_path']
    );
  }

  chainInputChanged() {
    this.formsDefinition.meta.bChainInput = this.chainInput;
  }

  resetForm() {
    // les valeur que l'on garde d'une saisie à l'autre
    const keep = this.config['keep'] || [];
    const formKey = Object.keys(this.form.value);

    for (const key of formKey) {
      if (key in keep) this.form.patchValue({ key: null });
    }
    this.object = null;

    // this.obj = this.setQueryParams(this.obj);

    this.form.patchValue({ geometry: null });
    this.initForm();
  }

  onCancelEdit() {
    // this.EditChange.emit(false);
    // this._location.back();
    if (this.object) {
      this.object.geometry == null
        ? this._geojsonService.setMapDataWithFeatureGroup([this._geojsonService.sitesFeatureGroup])
        : this._geojsonService.setMapBeforeEdit(this.object.geometry);
    }
    this.navigateToDetail();
  }

  ngOnDestroy() {
    this.form.patchValue({ geometry: null });
    this._formService.changeFormMapObj({
      frmGp: null,
      geometry_type: null,
    });
  }
}
