import { Injectable } from '@angular/core';
import { BehaviorSubject,ReplaySubject, Observable, forkJoin, of } from 'rxjs';
import { concatMap } from 'rxjs/operators';

import { ISite, ISitesGroup } from '../interfaces/geom';
import { JsonData } from '../types/jsondata';
import { Utils } from '../utils/utils';
import { MonitoringObjectService } from './monitoring-object.service';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { IExtraForm, IFormMap } from '../interfaces/object';


@Injectable()
export class FormService {
  data: JsonData = {};
  frmCtrl: FormControl = new FormControl(null);
  frmCtrlName: string = '';
  private dataSub = new BehaviorSubject<object>(this.data);
  private formCtrl = new BehaviorSubject<IExtraForm>({frmCtrl : this.frmCtrl,frmName:this.frmCtrlName});
  currentData = this.dataSub.asObservable();
  currentExtraFormCtrl = this.formCtrl.asObservable();
  properties: JsonData = {};
  moduleCode: string;
  objecType: string;

  frmrGrp: FormGroup = this._formBuilder.group({});
  private formMap = new BehaviorSubject<IFormMap>({frmGp:this.frmrGrp ,bEdit:true,obj:{}});
  currentFormMap = this.formMap.asObservable();

  constructor(private _objService: MonitoringObjectService, private _formBuilder: FormBuilder) {}


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

  changeExtraFormControl(formCtrl:FormControl,formCtrlName:string){
    this.formCtrl.next({frmCtrl:formCtrl,frmName:formCtrlName})
  }

  changeFormMapObj(formMapObj:IFormMap){
    this.formMap.next(formMapObj)
  }

  formValues(obj): Observable<any> {
    // const {properties ,remainaing} = obj
    const properties = Utils.copy(obj.properties);
    const observables = {};
    const schema = obj[obj.moduleCode];
    
    // ADD specific properties if exist
    if (obj.specific != undefined){
      for (const attribut_name of Object.keys(obj.specific)) {
        properties[attribut_name] = obj[attribut_name];
      }
    }


    for (const attribut_name of Object.keys(schema)) {
      const elem = schema[attribut_name];
      if (!elem.type_widget) {
        continue;
      }
      observables[attribut_name] = this._objService.toForm(elem, properties[attribut_name]);
    }

    return forkJoin(observables).pipe(
      concatMap((formValues_in) => {
        const formValues = Utils.copy(formValues_in);
        // geometry
        if (obj.config["geometry_type"]) {
          // TODO: change null by the geometry load from the object (if edit) or null if create
          // formValues["geometry"] = this.geometry; // copy???
          formValues["geometry"] = null ; // copy???
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
    if (obj.id_relationship != undefined) {
      for (const [key, value] of Object.entries(obj.id_relationship)) {
        if (typeof value == 'string') {
          if (obj[value] != undefined) {
            postData['properties'][value] = obj[value];
          } else if (Object.keys(obj.dataComplement).includes(value)) {
            postData['properties'][value] = obj.dataComplement[value];
          }
        }
      }
    }

    //   properties: propertiesData,
    //   // id_parent: this.parentId
    // };

    // TODO: A voir q'il faut remettre
    if (obj.config["geometry_type"]) {
      postData["geometry"] = formValue["geometry"];
      postData["type"] = "Feature";
    }
    return postData;
  }
}
