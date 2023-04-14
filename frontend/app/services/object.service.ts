import { Injectable } from "@angular/core";
import { BehaviorSubject,ReplaySubject } from "rxjs";
import { endPoints } from "../enum/endpoints";
import { ISitesGroup, ISiteType } from "../interfaces/geom";
import { IobjObs, ObjDataType } from "../interfaces/objObs";
import { JsonData } from "../types/jsondata";


@Injectable()
export class ObjectService {
  objObs: IobjObs<ObjDataType>;
  private objSelected =  new ReplaySubject<any>(1);
  currentObjSelected = this.objSelected.asObservable();

  private dataObjType = new ReplaySubject<IobjObs<JsonData>>(1);
  currentObjectType = this.dataObjType.asObservable();

  private dataObjTypeParent = new ReplaySubject<IobjObs<JsonData>>(1);
  currentObjectTypeParent = this.dataObjTypeParent.asObservable();

  constructor() {
    let storedObjectType = localStorage.getItem('storedObjectType');
    let storedObjectTypeParent = localStorage.getItem('storedObjectTypeParent');
    let storedObjectSelected= localStorage.getItem('storedObjectSelected');
    if (storedObjectType)
        this.changeObjectType(JSON.parse(storedObjectType), false);

    if (storedObjectTypeParent)
        this.changeObjectTypeParent(JSON.parse(storedObjectTypeParent), false);
        
    if (storedObjectSelected)
        this.changeSelectedObj(JSON.parse(storedObjectSelected), false);
}


  changeObjectType(newObjType: IobjObs<JsonData>,storeObjectType: boolean = false) {
    if (storeObjectType)
      localStorage.setItem('storedObjectType', JSON.stringify(newObjType));
     this.dataObjType.next(newObjType);
  }

   changeObjectTypeParent(newObjType: IobjObs<JsonData>,storeObjectTypeParent: boolean = false) {
    if (storeObjectTypeParent)
      localStorage.setItem('storedObjectTypeParent', JSON.stringify(newObjType));
     this.dataObjTypeParent.next(newObjType);
  }

  changeSelectedObj(newObjSelected:ObjDataType , storeObjectTypeSelected: boolean = false ){
    if (storeObjectTypeSelected)
      localStorage.setItem('storedObjectSelected', JSON.stringify(newObjSelected));
     this.objSelected.next(newObjSelected);
  }
}
