import { Component, OnInit, Input, OnChanges, Output, EventEmitter } from '@angular/core';
import { ApiService } from '../../services/api-geom.service';
import { MonitoringObjectG } from '../../class/monitoring-object-g';
import { FormGroup, FormBuilder, Validators, FormControl, FormArray } from '@angular/forms';
import { CommonService } from '@geonature_common/service/common.service';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';
import { FormService } from '../../services/form.service';
import { DataUtilsService } from '../../services/data-utils.service';

@Component({
  selector: 'pnx-monitoring-form-g',
  templateUrl: './monitoring-form-g.component.html',
  styleUrls: ['./monitoring-form-g.component.css'],
})
export class MonitoringFormGComponent implements OnChanges {
  @Input() apiService: ApiService;
  @Input() obj: MonitoringObjectG;
  @Input() form: FormGroup = new FormGroup('');
  @Input() config: any;

  public meta: any;
  public saveAndAddChildrenSpinner: boolean = false;
  public saveSpinner: boolean = false;
  public chainInput: boolean = false;
  public canUpdate: boolean = false;
  public addChildren: boolean = false;

  constructor(
    public _commonService: CommonService,
    public _formService: FormService,
    public _dataUtilsService: DataUtilsService,
    private _dynformService: DynamicFormService,
  ) {}

  ngOnChanges() {
    if (this.config) {
      console.log(this.config);
    }
    if (this.obj) {
      console.log(this.obj);
    }
  }

  ngOnInit() {
    // Initialisation des variables
    // this.initializeVariables(this.obj);

    // Initialisation des permissions de l'utilisateur courant
    // this.initPermission();

    // Récupération de la configuration du module

    // this.initializeSpecificConfig(this.obj.config['generic'], this.obj.config['specific']);

    // // Initialisation des paramètres par défaut du formulaire
    // this.queryParams = this._route.snapshot.queryParams || {};

    this.meta = {
      nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
      dataset: this._dataUtilsService.getDataUtil('dataset'),
      // id_role: this.currentUser.id_role,
      bChainInput: this.chainInput,
      // parents: this.obj.parents,
    };

    // // Récupération de la définition du formulaire
    // this.objFormsDefinition = this.initObjFormDefiniton(this.confiGenericSpec, this.meta);
    // // Tri des proprités en fonction de la variable display_properties
    // this.displayProperties = [...(this.obj.configParam('display_properties') || [])];
    // this.objFormsDefinition = this.sortObjFormDefinition(
    // this.displayProperties,
    // this.objFormsDefinition
    // );

    // if (this.obj.config['geometry_type']) {
    // const validatorRequired =
    //     this.obj.objectType == 'sites_group'
    //     ? this._formBuilder.control('')
    //     : this._formBuilder.control('', Validators.required);

    // let frmCtrlGeom = {
    //     frmCtrl: validatorRequired,
    //     frmName: 'geometry',
    // };

    // this.form = this._formService.addFormCtrlToObjForm(frmCtrlGeom, this.form);
    // }
    // // Conversion des query params de type entier mais en string en int
    // //  ??? A comprendre
    // this.obj = this.setQueryParams(this.obj);
    // this.initObjFormValues(this.obj, this.confiGenericSpec, Array.from(this.idsTypesSite))

    // console.log('Patching the object form values');
    // this.objForm.patchValue(genericFormValues);
    // if (specificFormValues !== null) {
    //   this._formService.patchValuesInDynamicGroups(
    //     specificFormValues,
    //     this.objFormsDynamic
    //   );
    // }
    // this.obj.bIsInitialized = true;
    // const dynamicGroupsArray = this.objForm.get('dynamicGroups') as FormArray;
    // if (dynamicGroupsArray) this.subscribeToDynamicGroupsChanges(dynamicGroupsArray);
    // this.setDefaultFormValue();
  }

  onFormValueChange(event) {
    const change = this.obj.change();
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objForm, meta: this.meta });
    }, 100);
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

  initForm() {}

  notAllowedMessage() {}

  onSubmit(isAddChildrend = false) {
    isAddChildrend ? (this.saveAndAddChildrenSpinner = true) : (this.saveSpinner = true);

    let objFormValueGroup = this.form.value;

    let actionLabel = '';
    let action;
    if (this.obj) {
      action = this.apiService.patch;
      actionLabel = 'Modification';
    } else {
      action = this.apiService.create;
      actionLabel = 'Création';
    }

    action.subscribe((objData) => {
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
        // this.navigateToAddChildren();
      } else {
        if (true) {
          // if (this.obj.configParam('redirect_to_parent')) {
          console.log('this.navigateToParent()');
          // this.navigateToParent();
        } else {
          console.log('this.navigateToDetail()');
          // this.navigateToDetail();
        }
      }
    });
  }

  onCancelEdit() {}
}
