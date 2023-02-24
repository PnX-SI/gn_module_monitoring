import { Injectable } from "@angular/core";
import { BehaviorSubject } from "rxjs";

@Injectable()
export class ObjectService {
  objectType: string = "";
  private dataObjType = new BehaviorSubject<string>(this.objectType);
  currentObjectType = this.dataObjType.asObservable();
  
  objectTypeParent: string = "";
  private dataObjTypeParent = new BehaviorSubject<string>(this.objectTypeParent);
  currentObjectTypeParent = this.dataObjTypeParent.asObservable();

  constructor() {}

  changeObjectType(newObjType: string) {
    this.dataObjType.next(newObjType);
  }

  changeObjectTypeParent(newObjType: string) {
    this.dataObjTypeParent.next(newObjType);
  }
}
