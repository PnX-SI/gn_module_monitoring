import { Injectable } from '@angular/core';

import { IColumn } from '../interfaces/column';

interface ItemObjectTable {
  id: number | null;
  selected: boolean;
  visible: boolean;
  current: boolean;
}

type ItemsObjectTable = { [key: string]: ItemObjectTable };

@Injectable()
export class DataTableService {
  obj: ItemsObjectTable;
  objectsStatus: ItemsObjectTable;
  rowStatus: ItemObjectTable;
  idObj: number;

  // IF prefered observable compare to ngOnChanges uncomment this:
  // dataCol:IColumn[] =[{prop:"",name:"",description:""}]
  // private dataCols = new BehaviorSubject<object>(this.dataCol);
  // currentCols = this.dataCols.asObservable();

  constructor() {}

  // IF prefered observable compare to ngOnChanges uncomment this:
  // changeColsTable(newCols:IColumn[],newRows){
  //   const arr = Object.keys(newCols);
  //   const allColumn: IColumn[] = arr
  //     .filter((item) => Object.keys(newRows).includes(item))
  //     .map((elm) => ({
  //       name: newCols[elm],
  //       prop: elm,
  //       description: elm,
  //     }));
  //   this.dataCols.next(allColumn)
  // }

  colsTable(colName: {}): IColumn[] {
    const arr = Object.keys(colName);
    const allColumn: IColumn[] = arr.map((elm) => ({
      name: colName[elm],
      prop: elm,
      description: elm,
    }));
    return allColumn;
  }

  initObjectsStatus(objList, key): ItemObjectTable[] {
    const objectsStatus = {};
    objectsStatus[key] = [];
    objectsStatus[key] = objList.map((obj) => ({
      id: obj[obj['pk']],
      selected: false,
      visible: true,
      current: false,
    }));
    // }

    // TODO: Comprendre cette partie à quoi elle sert
    // init site status
    // if (this.idObj) {
    //   objectsStatus[key] = [];
    //   objList.features.forEach((f) => {
    //     // determination du site courrant
    //     let cur = false;
    //     if (f.properties.id_sites_group == this.idObj) {
    //       cur = true;
    //     }

    //     objectsStatus[key].push({
    //       id: f.properties.id_sites_group,
    //       selected: false,
    //       visible: true,
    //       current: cur,
    //     });
    //   });
    // }

    // this.rowStatus = this.objectsStatus[key];

    return objectsStatus[key];
  }
}
