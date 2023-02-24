import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable, of, forkJoin } from "rxjs";
import { concatMap } from "rxjs/operators";

import { JsonData } from "../types/jsondata";

import { Utils } from "../utils/utils";
import { MonitoringObjectService } from "./monitoring-object.service";

@Injectable()
export class EditObjectService {
  data: JsonData = {};
  private dataSub = new BehaviorSubject<object>(this.data);
  currentData = this.dataSub.asObservable();
  properties: JsonData;
  moduleCode:string;
  objecType:string;

  constructor(
      private _objService:MonitoringObjectService
  ) {}

  changeDataSub(newDat: JsonData) {
    this.properties = newDat;
    newDat.moduleCode = "generic";
    newDat.objectType = "sites_group";
    this.moduleCode=  "generic";
    this.objecType=  "sites_group"
    this.dataSub.next(newDat)
    
  }



  formValues(obj): Observable<any> {
    const properties = Utils.copy(this.properties);
    const observables = {};
    const schema = obj[this.moduleCode];
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
}
