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

  colsTable(colName: {}, dataTable): IColumn[] {
    const arr = Object.keys(colName);
    const allColumn: IColumn[] = arr
      .filter((item) => Object.keys(dataTable).includes(item))
      .map((elm) => ({
        name: colName[elm],
        prop: elm,
        description: elm,
      }));
    return allColumn;
  }

  initObjectsStatus(obj, key) {
    const objectsStatus = {};
    // for (const childrenType of Object.keys(this.obj.children)) {
    objectsStatus[key] = obj.map((groupSite) => {
      return {
        id: groupSite.id_sites_group,
        selected: false,
        visible: true,
        current: false,
      };
    });
    // }

    // init site status
    if (this.idObj) {
      objectsStatus[key] = [];
      obj.features.forEach((f) => {
        // determination du site courrant
        let cur = false;
        if (f.properties.id_sites_group == this.idObj) {
          cur = true;
        }

        objectsStatus[key].push({
          id: f.properties.id_sites_group,
          selected: false,
          visible: true,
          current: cur,
        });
      });
    }

    this.objectsStatus = objectsStatus;
    this.rowStatus = this.objectsStatus[key];
    return [this.objectsStatus, this.rowStatus];
  }
}
