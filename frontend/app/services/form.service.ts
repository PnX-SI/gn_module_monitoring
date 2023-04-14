import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, forkJoin, of } from 'rxjs';
import { concatMap } from 'rxjs/operators';

import { ISite, ISitesGroup } from '../interfaces/geom';
import { IobjObs, ObjDataType } from '../interfaces/objObs';
import { JsonData } from '../types/jsondata';
import { Utils } from '../utils/utils';
import { MonitoringObjectService } from './monitoring-object.service';

@Injectable()
export class FormService {
  data: JsonData = {};
  private dataSub = new BehaviorSubject<object>(this.data);
  currentData = this.dataSub.asObservable();
  properties: JsonData = {};
  moduleCode: string;
  objecType: string;

  constructor(private _objService: MonitoringObjectService) {}

  // TODO: voir si nécessaire de garder ça (objService permet d'avoir le bon objet ? et sinon modifier pour obtenir ce qu'il faut en formulaire)
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

  formValues(obj): Observable<any> {
    // const {properties ,remainaing} = obj
    const properties = Utils.copy(this.properties);
    const observables = {};
    const schema = obj[obj.moduleCode];
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
        // if (this.config["geometry_type"]) {
        //   formValues["geometry"] = this.geometry; // copy???
        // }
        return of(formValues);
      })
    );
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
    // if (this.config["geometry_type"]) {
    //   postData["geometry"] = formValue["geometry"];
    //   postData["type"] = "Feature";
    // }
    return postData;
  }
}
