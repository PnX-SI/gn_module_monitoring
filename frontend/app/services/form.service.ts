import { Injectable } from '@angular/core';
import { BehaviorSubject, ReplaySubject, Observable, forkJoin, of } from 'rxjs';
import { concatMap } from 'rxjs/operators';

import { ISite, ISitesGroup } from '../interfaces/geom';
import { JsonData } from '../types/jsondata';
import { Utils } from '../utils/utils';
import { MonitoringObjectService } from './monitoring-object.service';
import { FormBuilder, FormControl, FormGroup, FormArray, AbstractControl } from '@angular/forms';
import { IExtraForm, IFormMap } from '../interfaces/object';
import { ConfigService } from './config.service';

@Injectable()
export class FormService {


  frmrGrp: FormGroup = this._formBuilder.group({});

  // Observable qui contient l'objet form et l'objet courant
  //  utilisé par map-list pour afficher le formulaire geographique de l'objet sélectionné
  // Seul le type de géométrie et le controle geometry sont utilisés actuellement
  //  TODO: réduire les informations stockées dans cet observable
  private formMap = new BehaviorSubject<IFormMap>({ frmGp: this.frmrGrp, obj: {} });
  currentFormMap = this.formMap.asObservable();

  // Observable qui contient le mode édition courant (true/false)
  private currentEdit = new BehaviorSubject<boolean>(false);
  currentEditMode = this.currentEdit.asObservable();

  constructor(
    private _objService: MonitoringObjectService,
    private _formBuilder: FormBuilder,
    private _configService: ConfigService
  ) {}


  changeFormMapObj(formMapObj: IFormMap) {
    this.formMap.next(formMapObj);
  }

  changeCurrentEditMode(editMode: boolean) {
    this.currentEdit.next(editMode);
  }

  formValues(obj, schemaUpdate = {}): Observable<any> {
    let schema;
    // const {properties ,remainaing} = obj
    const properties = Utils.copy(obj.properties);
    const observables = {};
    if (obj.moduleCode && Object.keys(schemaUpdate).length != 0) {
      schema = schemaUpdate;
    } else if (obj.moduleCode) {
      schema = this._configService.schema(obj.moduleCode, obj.objectType, 'all');
    } else {
      schema = obj[obj.moduleCode];
    }

    // ADD specific properties if exist
    if (obj.specific != undefined) {
      for (const attribut_name of Object.keys(obj.specific)) {
        properties[attribut_name] = obj[attribut_name];
      }
    }

    for (const attribut_name of Object.keys(schema)) {
      const elem = schema[attribut_name];
      // NOTES: [dev-suivi-eol] ici le formValues possédant uniquement des propriétés sans type_widget ne surcouchent pas les champs specific au type de site
      if (!(elem || [])['type_widget']) {
        continue;
      }
      observables[attribut_name] = this._objService.toForm(elem, properties[attribut_name]);
    }

    return forkJoin(observables).pipe(
      concatMap((formValues_in) => {
        const formValues = Utils.copy(formValues_in);
        // geometry
        if ('config' in obj && obj.config['geometry_type']) {
          // TODO: change null by the geometry load from the object (if edit) or null if create
          // formValues["geometry"] = this.geometry; // copy???
          formValues['geometry'] = obj.geometry; // copy???
        }
        return of(formValues);
      })
    );
  }

  /**
   * Add a form control to the object form.
   *
   * @param {Object} frmCtrl - The form control to add to the object form
   * @param {FormGroup} objForm - The object form to add the form control to
   * @return {Observable<FormGroup>} The updated object form
   */
  addFormCtrlToObjForm(
    frmCtrl: { frmCtrl: FormControl; frmName: string },
    objForm: FormGroup
  ): FormGroup {
    if (frmCtrl.frmName in objForm.controls) {
      // Si le champ existe déjà dans l'objet form, on ne fait rien
    } else {
      objForm.addControl(frmCtrl.frmName, frmCtrl.frmCtrl);
    }
    return objForm;
  }

  /**
   * Add multiple form groups to the object form.
   *
   * @param {Object} formGroups - Object containing form groups to add
   * @param {FormGroup} targetForm - The target form group to add form groups to
   * @return {FormGroup} The updated target form group
   */
  addMultipleFormGroupsToObjForm(
    formGroups: { [key: string]: FormGroup },
    targetForm: FormGroup
  ): FormGroup {
    // TODO ANALYSER ce qui est réeelement nécessaire
    let dynamicGroups = targetForm.get('dynamicGroups') as FormArray;

    if (!dynamicGroups) {
      dynamicGroups = this._formBuilder.array([]);
      targetForm.addControl('dynamicGroups', dynamicGroups);
      dynamicGroups = targetForm.get('dynamicGroups') as FormArray; // Refresh reference after adding it
    }

    for (let i = dynamicGroups.controls.length - 1; i >= 0; i--) {
      const control = dynamicGroups.controls[i];
      const controlName = control.get('name')?.value;
      if (!formGroups[controlName]) {
        dynamicGroups.removeAt(i);
      }
    }

    for (const key in formGroups) {
      const existingControlIndex = dynamicGroups.controls.findIndex(
        (control) => control.get('name')?.value === key
      );

      if (existingControlIndex !== -1) {
        dynamicGroups.controls[existingControlIndex].patchValue(formGroups[key].value, {
          emitEvent: false,
        });
      } else {
        const newControl = formGroups[key];
        newControl.addControl('name', this._formBuilder.control(key)); // Adding control with key as 'name'
        dynamicGroups.push(newControl);
      }
    }
    return targetForm;
  }

  /**
   * Patches values inside dynamic form groups
   *
   * @param valuesToPatch Values to patch, with the key being the control name and the value
   * being the new value to set
   * @param objOfFormGroups Object containing form groups to patch, with the key being the group name
   * and the value being the form group
   */
  patchValuesInDynamicGroups(
    valuesToPatch: { [controlName: string]: any },
    objOfFormGroups: { [groupName: string]: FormGroup }
  ): void {
    Object.keys(objOfFormGroups).forEach((groupName) => {
      const formGroup = objOfFormGroups[groupName];
      if (formGroup instanceof FormGroup) {
        this.patchValuesInFormGroup(formGroup, valuesToPatch);
      }
    });
  }

  /**
   * Patches values inside a form group
   *
   * @param formGroup Form group to patch values in
   * @param valuesToPatch Values to patch, with the key being the control name and the value
   * being the new value to set
   */
  patchValuesInFormGroup(formGroup: FormGroup, valuesToPatch: JsonData): void {
    Object.keys(valuesToPatch).forEach((controlName) => {
      if (formGroup.contains(controlName)) {
        formGroup.get(controlName).patchValue(valuesToPatch[controlName]);
      }
    });
  }

  /**
   * Flattens a FormGroup into a JSON object.
   * @param formGroup The FormGroup to flatten.
   * @returns The flattened FormGroup as a JSON object.
   */
  flattenFormGroup(formGroup: FormGroup): JsonData {
    const flatObject: JsonData = {}; // JSON object to return

    // Recursive function to process nested controls
    /**
     * Flattens a control (or controls within a FormGroup or FormArray) into the
     * flattened JSON object.
     * @param control The control (or FormGroup or FormArray) to flatten.
     * @param keyPrefix The prefix of the control's key to use in the flattened
     * object.
     */
    const flattenControl = (control: AbstractControl, keyPrefix: string = ''): void => {
      if (control instanceof FormGroup) {
        // If control is a FormGroup, recurse into its controls and flatten each one
        Object.entries(control.controls).forEach(([controlName, nestedControl]) => {
          flattenControl(nestedControl, `${controlName}.`);
        });
      } else if (control instanceof FormArray) {
        // If control is a FormArray, recurse into each control in the FormArray
        control.controls.forEach((arrayControl, index) => {
          flattenControl(arrayControl, `${keyPrefix}`);
        });
      } else {
        // If control is not a FormGroup or FormArray, add it to the flattened object
        flatObject[keyPrefix.slice(0, -1)] = control.value;
      }
    };

    // Start flattening from the root FormGroup
    flattenControl(formGroup);

    return flatObject;
  }
}
