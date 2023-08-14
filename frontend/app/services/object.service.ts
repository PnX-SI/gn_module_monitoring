import { Injectable } from '@angular/core';
import { ReplaySubject } from 'rxjs';
import { IobjObs, ObjDataType } from '../interfaces/objObs';
import { JsonData } from '../types/jsondata';
import { IBreadCrumb, SelectObject } from '../interfaces/object';

@Injectable()
export class ObjectService {
  objObs: IobjObs<ObjDataType>;
  private objSelected = new ReplaySubject<any>(1);
  currentObjSelected = this.objSelected.asObservable();

  private parentObjSelected = new ReplaySubject<any>(1);
  currentParentObjSelected = this.parentObjSelected.asObservable();

  private dataObjType = new ReplaySubject<IobjObs<JsonData>>(1);
  currentObjectType = this.dataObjType.asObservable();

  private dataObjTypeParent = new ReplaySubject<IobjObs<JsonData>>(1);
  currentObjectTypeParent = this.dataObjTypeParent.asObservable();

  private dataBreadCrumb = new ReplaySubject<IBreadCrumb[]>(1);
  currentDataBreadCrumb = this.dataBreadCrumb.asObservable();

  private dataListOption = new ReplaySubject<SelectObject[]>(1);
  currentListOption = this.dataListOption.asObservable();

  constructor() {
    let storedObjectType = localStorage.getItem('storedObjectType');
    let storedObjectTypeParent = localStorage.getItem('storedObjectTypeParent');
    let storedObjectSelected = localStorage.getItem('storedObjectSelected');
    let storedParentObjectSelected = localStorage.getItem('storedParentObjectSelected');
    let storedDataBreadCrumb = localStorage.getItem('storedDataBreadCrumb');
    if (storedObjectType) this.changeObjectType(JSON.parse(storedObjectType), false);

    if (storedObjectTypeParent)
      this.changeObjectTypeParent(JSON.parse(storedObjectTypeParent), false);

    if (storedObjectSelected) this.changeSelectedObj(JSON.parse(storedObjectSelected), false);

    if (storedParentObjectSelected)
      this.changeSelectedObj(JSON.parse(storedParentObjectSelected), false);

    if (storedDataBreadCrumb) this.changeBreadCrumb(JSON.parse(storedDataBreadCrumb), false);
  }

  changeObjectType(newObjType: IobjObs<JsonData>, storeObjectType: boolean = false) {
    if (storeObjectType) localStorage.setItem('storedObjectType', JSON.stringify(newObjType));
    this.dataObjType.next(newObjType);
  }

  changeObjectTypeParent(newObjType: IobjObs<JsonData>, storeObjectTypeParent: boolean = false) {
    if (storeObjectTypeParent)
      localStorage.setItem('storedObjectTypeParent', JSON.stringify(newObjType));
    this.dataObjTypeParent.next(newObjType);
  }

  changeSelectedObj(newObjSelected: ObjDataType | {}, storeObjectTypeSelected: boolean = false) {
    if (storeObjectTypeSelected)
      localStorage.setItem('storedObjectSelected', JSON.stringify(newObjSelected));
    this.objSelected.next(newObjSelected);
  }

  changeSelectedParentObj(
    newObjParentSelected: ObjDataType | {},
    storeParentObjectTypeSelected: boolean = false
  ) {
    if (storeParentObjectTypeSelected)
      localStorage.setItem('storedParentObjectSelected', JSON.stringify(newObjParentSelected));
    this.parentObjSelected.next(newObjParentSelected);
  }

  changeBreadCrumb(newDataBreadCrumb: IBreadCrumb[], storeDataBreadCrumb: boolean = false) {
    if (storeDataBreadCrumb)
      localStorage.setItem('storedDataBreadCrumb', JSON.stringify(newDataBreadCrumb));
    this.dataBreadCrumb.next(newDataBreadCrumb);
  }

  changeListOption(newListOption: SelectObject[]) {
    this.dataListOption.next(newListOption);
  }
}
