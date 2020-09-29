import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { MonitoringObject } from '../../class/monitoring-object';
import { Router } from '@angular/router';
import { ConfigService } from '../../services/config.service';
import { CommonService } from '@geonature_common/service/common.service';


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

  keepNames = [];

  public bSaveSpinner = false;
  public bSaveAndAddChildrenSpinner = false;
  public bDeleteSpinner = false;
  public bDeleteModal = false;
  public bChainInput = false;
  public bAddChildren = false;

  constructor(
    private _formBuilder: FormBuilder,
    private _router: Router,
    private _configService: ConfigService,
    private _commonService: CommonService,
  ) { }

  ngOnInit() {
    this._configService.init(this.obj.moduleCode).subscribe(() => {
      this.bChainInput = this._configService.frontendParams()['bChainInput'];
      const schema = this.obj.schema();

      // init objFormsDefinition
      this.objFormsDefinition = Object.keys(schema)
        // medias toujours à la fin
        .sort((a, b) => {
          return a === 'medias' ? +1 : b === 'medias' ? -1 : 0;
        })
        .filter((attribut_name) => schema[attribut_name].type_widget)
        .map((attribut_name) => {
          const elem = schema[attribut_name];
          elem['attribut_name'] = attribut_name;
          return elem;
        });
      // set geometry
      if (this.obj.config['geometry_type']) {
        this.objForm.addControl(
          'geometry',
          this._formBuilder.control('', Validators.required)
        );
      }
      this.initForm();
    });
  }

  /** pour réutiliser des paramètres déjà saisis */
  keepDefinitions() {
    return this.objFormsDefinition.filter((def) =>
      this.obj.configParam('keep').includes(def.attribut_name)
    );
  }

  /** initialise le formulaire quand le formulaire est prêt ou l'object est prêt */
  initForm() {
    if (!(this.objForm && this.obj.bIsInitialized)) {
      return;
    }
    this.obj.formValues().subscribe((formValue) => {
      console.log('init obj');
      this.objForm.patchValue(formValue);
      this.setDefaultFormValue();
    });
  }

  resetObjForm() {
    const keep = {};
    for (const key of this.keepNames) {
      keep[key] = this.obj.properties[key];
    }

    // TODO à faire comme il faut (popup config pour les valeurs à garder)
    console.log('keep', keep);

    const parentId = this.obj.parentId;
    this.obj = new MonitoringObject(
      this.obj.moduleCode,
      this.obj.objectType,
      null,
      this.obj.monitoringObjectService()
    );

    this.obj.properties[this.obj.configParam('id_field_Name')] = null;
    this.obj.parentId = parentId;
    this.obj.get(0).subscribe(() => {
      this.obj.bIsInitialized = true;
      for (const key of this.keepNames) {
        this.obj.properties[key] = keep[key];
      }
      this.initForm();
    });
  }

  /** Pour donner des valeurs par defaut si la valeur n'est pas définie
   * ici id_digitiser => current_user.id_role
   */
  setDefaultFormValue() {
    const values = this.objForm.value;
    const defaultValues = {};

    defaultValues['id_digitiser'] =
      values['id_digitiser'] || this.currentUser.id_role;
    this.objForm.patchValue(defaultValues);
  }

  /**
   * TODO faire des fonctions dans monitoring objet (ou moniotring objet service pour naviguer
   */

  /**
   * Valider et renseigner les enfants
   */
  navigateToAddChildren() {
    this.bEditChange.emit(false);
    this._router.navigate([
      '/',
      this._configService.frontendModuleMonitoringUrl(),
      'create_object',
      this.obj.moduleCode,
      this.obj.uniqueChildrenType(),
      this.obj.id,
    ]);
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToDetail() {
    this.bEditChange.emit(false); // patch bug navigation
    this._router.navigate([
      '/',
      this._configService.frontendModuleMonitoringUrl(),
      'object',
      this.obj.moduleCode,
      this.obj.objectType,
      this.obj.id,
    ]);
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToParent() {
    this.bEditChange.emit(false); // patch bug navigation

    // cas module
    if (this.obj.objectType.includes('module')) {
      this._router.navigate([
        '/',
        this._configService.frontendModuleMonitoringUrl(),
        'object',
        this.obj.moduleCode,
        'module',
        this.obj.id,
      ]);

      // autres cas
    } else {
      this._router.navigate([
        '/',
        this._configService.frontendModuleMonitoringUrl(),
        'object',
        this.obj.moduleCode,
        this.obj.parentType(),
        this.obj.parentId,
      ]);
    }
  }

  /** TODO remove */
  // reload_create_route() {
  //   this._router.navigate(['/']);
  //   setTimeout(() => {
  //     this._router.navigate([
  //       '/',
  //       this._configService.frontendModuleMonitoringUrl(),
  //       'create_object',
  //       this.obj.moduleCode,
  //       this.obj.objectType,
  //       this.obj.parentId,
  //     ]);
  //   }, 100);
  // }

  /** TODO améliorer */
  testChoixSite() {
    const bCreation = !this.obj.id;
    const bChoixSite =
      this.obj.schema()['id_base_site'] &&
      this.obj.schema()['id_base_site'].type_widget === 'site';
    return bCreation && bChoixSite && this.bChainInput;
  }

  /** TODO améliorer site etc.. */
  onSubmit() {
    // cas choix site
    if (this.testChoixSite()) {
      this.obj.parentId = this.objForm.value['id_base_site'];
    }

    const action = this.obj.id
      ? this.obj.patch(this.objForm.value)
      : this.obj.post(this.objForm.value);
    const actionLabel = this.obj.id ? 'Modification' : 'Création';
    action.subscribe((objData) => {
      // TODO toaster service
      console.log(
        'info',
        `${actionLabel} de ${this.obj.configParam('label')} ${
        this.obj.id
        } effectué`
      );
      this._commonService.regularToaster('success', `${actionLabel} de ${this.obj.configParam('label')} ${
        this.obj.id
        } effectué`);
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
        this.navigateToDetail();
      }
    });
  }

  onCancelEdit() {
    if (this.obj.id) {
      this.bEditChange.emit(false);
    } else {
      this.navigateToParent();
    }
  }

  onDelete() {
    this.bDeleteSpinner = true;
    const msg_delete = `${this.obj.template['label']} ${
      this.obj.id
      } supprimé. parent ${this.obj.parentType()} ${this.obj.parentId}`;
    console.log(msg_delete);
    this._commonService.regularToaster('info', msg_delete);


    this.obj.delete().subscribe((objData) => {
      this.bDeleteSpinner = this.bDeleteModal = false;
      this.objChanged.emit(this.obj);
      this.navigateToParent();
    });
  }

  /** bChainInput gardé dans config service */
  bChainInputChanged() {
    this._configService.setFrontendParams('bChainInput', this.bChainInput);
  }
}
