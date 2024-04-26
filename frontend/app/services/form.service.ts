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
  data: JsonData = {};
  frmCtrl: FormControl = new FormControl(null);
  frmCtrlName: string = '';
  private dataSub = new BehaviorSubject<object>(this.data);
  private dataSpec = new BehaviorSubject<object>(this.data);
  private dataSpecToCreate = new BehaviorSubject<object>(this.data);
  private formCtrl = new BehaviorSubject<IExtraForm>({
    frmCtrl: this.frmCtrl,
    frmName: this.frmCtrlName,
  });
  currentData = this.dataSub.asObservable();
  currentDataSpec = this.dataSpec.asObservable();
  currentDataSpecToCreate = this.dataSpecToCreate.asObservable();
  currentExtraFormCtrl = this.formCtrl.asObservable();
  properties: JsonData = {};
  moduleCode: string;
  objecType: string;

  frmrGrp: FormGroup = this._formBuilder.group({});
  private formMap = new BehaviorSubject<IFormMap>({ frmGp: this.frmrGrp, bEdit: false, obj: {} });
  currentFormMap = this.formMap.asObservable();

  constructor(
    private _objService: MonitoringObjectService,
    private _formBuilder: FormBuilder,
    private _configService: ConfigService
  ) {}

  changeDataSub(
    newDat: JsonData,
    objectType: string,
    endPoint: string,
    moduleCode: string = 'generic'
  ) {
    this.properties = newDat;
    newDat.moduleCode = moduleCode;
    newDat.objectType = objectType;
    newDat.endPoint = endPoint;
    this.dataSub.next(newDat);
  }

  dataToCreate(newDat: JsonData, urlRelative: string, moduleCode: string = 'generic') {
    newDat[moduleCode] = {};
    newDat.moduleCode = moduleCode;
    newDat.urlRelative = urlRelative;
    this.dataSub.next(newDat);
  }

  updateSpecificForm(newObj: JsonData, newPropSpec: JsonData) {
    const newObjandSpec = { newObj: newObj, propSpec: newPropSpec };
    this.dataSpec.next(newObjandSpec);
  }

  createSpecificForm(newPropSpec: JsonData) {
    this.dataSpecToCreate.next(newPropSpec);
  }

  changeExtraFormControl(formCtrl: FormControl, formCtrlName: string) {
    this.formCtrl.next({ frmCtrl: formCtrl, frmName: formCtrlName });
  }

  changeFormMapObj(formMapObj: IFormMap) {
    this.formMap.next(formMapObj);
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
      if (!elem.type_widget) {
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

  getProperties(formValue, obj): void {
    const propertiesData = {};
    const schema = obj[obj.moduleCode];
    for (const attribut_name of Object.keys(schema)) {
      const elem = schema[attribut_name];
      if (!elem.type_widget) {
        continue;
      }
      propertiesData[attribut_name] = this._objService.fromForm(elem, formValue[attribut_name]);
    }
  }

  // TODO: A voir si nécessaire d'utiliser le formatage des post et update data avant éxécution route coté backend
  postData(formValue, obj): { properties: ISitesGroup | ISite | any } {
    const propertiesData = {};
    const schema = obj[obj.moduleCode];
    for (const attribut_name of Object.keys(schema)) {
      const elem = schema[attribut_name];
      if (!elem.type_widget) {
        continue;
      }
      propertiesData[attribut_name] = this._objService.fromForm(elem, formValue[attribut_name]);
    }
    const postData = { properties: {} };
    if (obj.dataComplement == undefined) {
      postData['properties'] = propertiesData;
    } else {
      postData['properties'] = propertiesData;
      postData['dataComplement'] = obj.dataComplement;
    }

    // Ajout des id relationship
    // if (obj.id_relationship != undefined) {
    //   for (const [key, value] of Object.entries(obj.id_relationship)) {
    //     if (typeof value == 'string') {
    //       if (obj[value] != undefined) {
    //         postData['properties'][value] = obj[value];
    //       } else if (Object.keys(obj.dataComplement).includes(value)) {
    //         postData['properties'][value] = obj.dataComplement[value];
    //       }
    //     }
    //   }
    // }

    //   properties: propertiesData,
    //   // id_parent: this.parentId
    // };

    // TODO: A voir q'il faut remettre
    if (obj.config['geometry_type']) {
      postData['geometry'] = formValue['geometry'];
      // if(postData['geometry'] != null){
      postData['type'] = 'Feature';
      // }
    }
    return postData;
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
