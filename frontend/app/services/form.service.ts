import { Injectable } from '@angular/core';
import { BehaviorSubject, ReplaySubject, Observable, forkJoin, of } from 'rxjs';

import { concatMap, mergeMap } from 'rxjs/operators';

import { ISite, ISitesGroup } from '../interfaces/geom';
import { JsonData } from '../types/jsondata';
import { Utils } from '../utils/utils';
import { FormBuilder, FormControl, FormGroup, FormArray, AbstractControl } from '@angular/forms';
import { IExtraForm, IFormMap } from '../interfaces/object';
import { ConfigServiceG } from './config-g.service';
import { DataUtilsService } from './data-utils.service';

@Injectable()
export class FormService {
  // Observable qui contient l'objet control geometry du formulaire et le type de géométrie
  //  utilisé par draw-form pour afficher le formulaire geographique de l'objet sélectionné
  private formMap = new BehaviorSubject<IFormMap>({ frmGp: null, geometry_type: null });
  currentFormMap = this.formMap.asObservable();

  // Observable qui contient le mode édition courant (true/false)
  private currentEdit = new BehaviorSubject<boolean>(false);
  currentEditMode = this.currentEdit.asObservable();

  constructor(
    private _formBuilder: FormBuilder,
    private _configServiceG: ConfigServiceG,
    private _dataUtilsService: DataUtilsService
  ) {}

  changeFormMapObj(formMapObj: IFormMap) {
    this.formMap.next(formMapObj);
  }

  changeCurrentEditMode(editMode: boolean) {
    this.currentEdit.next(editMode);
  }

  toForm(elem, val): Observable<any> {
    let x = val;
    // valeur par default depuis la config schema
    x = [undefined, null].includes(x) ? (elem.value === '' ? null : elem.value) : x;
    if (elem.type_widget == 'date') {
      const date = new Date(x);
      x = x
        ? {
            year: date.getUTCFullYear(),
            month: date.getUTCMonth() + 1,
            day: date.getUTCDate(),
          }
        : null;
    } else if (elem.type_widget === 'observers') {
      const codeListObservers = this._configServiceG.codeListObservers();
      // Gestion des observateurs multiples
      if (!Array.isArray(val)) val = [val];

      x == null
        ? (x = [])
        : (x = this._dataUtilsService.getUsersByCodeList(codeListObservers).pipe(
            // Cas des observateurs multiples à gérer
            mergeMap((users: any) => {
              let currentUser = [];
              if (!Array.isArray(users)) {
                return of(null);
              }
              for (const user of users) {
                for (const obs of val) {
                  if (user.id_role == obs) {
                    currentUser.push(user);
                  }
                }
              }
              //Si non multiple on renvoie le premier élément ou null
              if (!elem.multi_select) {
                currentUser = currentUser.length ? currentUser[0] : null;
              }
              return of(currentUser);
            })
          ));
    } else if (elem.type_widget === 'taxonomy') {
      x = x ? this._dataUtilsService.getUtil('taxonomy', x, 'all') : null;
    } else if (
      elem.type_util === 'nomenclature' &&
      Utils.isObject(x) &&
      x.code_nomenclature_type &&
      x.cd_nomenclature
    ) {
      x = this._dataUtilsService.getNomenclature(x.code_nomenclature_type, x.cd_nomenclature).pipe(
        mergeMap((nomenclature) => {
          return of(nomenclature['id_nomenclature']);
        })
      );
    }

    x = x instanceof Observable ? x : of(x);
    return x;
  }

  fromForm(elem, val) {
    let x = val;
    if (x == undefined) {
      return x;
    }
    switch (elem.type_widget) {
      case 'date': {
        x =
          x && x.year && x.month && x.day
            ? `${x.year}-${String(x.month).padStart(2, '0')}-${String(x.day).padStart(2, '0')}`
            : null;
        break;
      }
      case 'observers': {
        if ('multi_select' in elem && elem.multi_select) {
          x = x.map((item) => {
            return item.id_role;
          });
        } else {
          x = x instanceof Array && x.length === 1 ? x[0].id_role : x.id_role;
        }
        break;
      }
      case 'taxonomy': {
        x = x instanceof Object ? x.cd_nom : x;
        break;
      }
    }
    return x;
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
