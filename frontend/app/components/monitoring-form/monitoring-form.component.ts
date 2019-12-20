import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from "@angular/forms";
import { MonitoringObject } from '../../class/monitoring-object';
import { Utils } from "../../utils/utils";
import { Router } from "@angular/router";
import { ConfigService } from "../../services/config.service";

@Component({
  selector: 'pnx-monitoring-form',
  templateUrl: './monitoring-form.component.html',
  styleUrls: ['./monitoring-form.component.css']
})
export class MonitoringFormComponent implements OnInit {

  @Input() currentUser;

  @Input() objForm: FormGroup;
  
  @Input() obj: MonitoringObject;
  @Output() objChange = new EventEmitter<MonitoringObject>();

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();


  objSchema;
  
  public bSaveSpinner = false;
  public bSaveAddSpinner = false;
  public bDeleteSpinner = false;
  public bDeleteModal = false;
  public circuitPointsData;
  public bChainInput = false;

  constructor(
    private _formBuilder: FormBuilder,
    private _router: Router,
    private _configService: ConfigService,
  ) { }

  ngOnInit() {
    this._configService.init(this.obj.modulePath)
      .flatMap(()=>{
        this.bChainInput = this._configService.frontendParams()['bChainInput']
        this.objSchema = this.obj.schema();
        return this.obj.formValues() 
      })
      .subscribe((formValues) => {
    // set geometry
    if (this.obj.config['geometry_type']) {
      let validator = !this.obj.isCircuit() ? Validators.required : null;
      this.objForm.addControl('geometry', this._formBuilder.control('', validator));
    }
    this.setFormValue(formValues);
  });
  }

  isFormReady() {
    let schemaFormSize = this.objSchema
      .filter( elem => elem.type_widget)
      .length;
    if (this.obj.config['geometry_type']) {
      schemaFormSize += 1;
    }
    let formSize = Utils.dictSize(this.objForm.controls);
    return schemaFormSize == formSize;
  }

  setFormValue(formValue) {
    let objFormChangeSubscription = this.objForm.valueChanges
      .subscribe(() => {
        if (this.isFormReady()) {
          objFormChangeSubscription.unsubscribe();

          if(this.obj.isObservationCircuit()) {
            this.objForm.addControl('code_circuit_point', this._formBuilder.control('', Validators.required));
            this.circuitPointsData = this.obj.circuitPoints && this.obj.circuitPoints.features.map(
              e => e.properties
            );
            formValue['code_circuit_point'] = this.obj.properties['code_circuit_point']
          }

          this.objForm.setValue(formValue);
          this.setDefaultFormValue()
          console.log('info', 'objForm initialisé')
        }
      })
    // emit change programmatically
    this.objForm.updateValueAndValidity({ onlySelf: false, emitEvent: true });
  }

  setDefaultFormValue() {
    const values = this.objForm.value
    let defaultValues = {};

    defaultValues['id_digitiser'] = values['id_digitiser'] || this.currentUser.id_role;
    this.objForm.patchValue(defaultValues);
  }

  navigateToParent() {
    if(this.obj.objectType.includes('module')) {
      this._router.navigate(['/', this._configService.frontendModuleMonitoringUrl()]);  
    }
    if(this.obj.parentType().includes('module')) {
      this._router.navigate(['/', this._configService.frontendModuleMonitoringUrl(), 'module', this.obj.modulePath]);
      return;
    } else {
      this._router.navigate(['/', this._configService.frontendModuleMonitoringUrl(), 'object', this.obj.modulePath, this.obj.parentType(), this.obj.parentId]);
      return; 
    }
  }

  reload_create_route() {

    this._router.navigate(['/']);
    setTimeout(()=> {
      this._router.navigate(['/', this._configService.frontendModuleMonitoringUrl(), 'create_object', this.obj.modulePath, this.obj.objectType, this.obj.parentId]);      this._router.navigate(['/', this._configService.frontendModuleMonitoringUrl(), 'create_object', this.obj.modulePath, this.obj.objectType, this.obj.parentId]);
        }, 100);
  }

  onSubmit(addNew=false) {
    this.bSaveSpinner = !addNew;
    this.bSaveAddSpinner = addNew;

    let action = this.obj.id ? this.obj.patch(this.objForm.value) : this.obj.post(this.objForm.value);
    let actionLabel = this.obj.id ? 'Modification' : 'Création';
    action.subscribe((objData) => {
            
      console.log('info', `${actionLabel} de ${this.obj.configParam('label')} ${this.obj.id} effectué`);
      this.bSaveSpinner = this.bSaveAddSpinner = false;
      this.bEditChange.emit(false);
      this.objChange.emit(this.obj);
      if (this.obj.objectType.includes('module')) {
        this._router.navigate(['/', this._configService.frontendModuleMonitoringUrl(), 'module', this.obj.modulePath]);
      } else {
        if(addNew) {
          this.reload_create_route();
        } else {
          this.navigateToParent();
          // let url = this._router.url;
          // this._router.navigate(['/', this._configService.frontendModuleMonitoringUrl(), 'object', this.obj.modulePath, this.obj.objectType, this.obj.id]);
        }
      }   
    });
  }

  onCancelEdit() {
    if(this.obj.id) {
      this.bEditChange.emit(false);
    } else {
      this.navigateToParent()
    }
  }

  onDelete() {
    this.bDeleteSpinner = true;
    let msg_delete = `${this.obj.template['label']} ${this.obj.id} supprimé. parent ${this.obj.parentType()} ${this.obj.parentId}`
    
    this.obj
    .delete()
    .subscribe((objData) => {
      console.log('info', msg_delete);
      this.bDeleteSpinner = this.bDeleteModal = false;
      this.navigateToParent();  
      });
    }

    bChainInputChanged() {
      this._configService.setFrontendParams('bChainInput', this.bChainInput)
    }
}
