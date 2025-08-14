import { Injectable } from '@angular/core';
import { ReplaySubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { IobjObs, ObjDataType } from '../interfaces/objObs';
import { JsonData } from '../types/jsondata';
import { IBreadCrumb, SelectObject } from '../interfaces/object';
import { DataMonitoringObjectService } from './data-monitoring-object.service';

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

  // comment
  private dataBreadCrumb = new ReplaySubject<IBreadCrumb[]>(1);
  currentDataBreadCrumb = this.dataBreadCrumb.asObservable();

  private dataListOption = new ReplaySubject<SelectObject[]>(1);
  currentListOption = this.dataListOption.asObservable();

  constructor(private _dataMonitoringObjectService: DataMonitoringObjectService) {
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

  loadBreadCrumb(
    moduleCode: string,
    objectType: string,
    id: number | null,
    queryParams: {},
    storeDataBreadCrumb: boolean = false
  ): void {
    /**
     * Charge les données du breadcrumb via un appel à l'API
     *   pour un module, un type d'objet et un ID spécifiques
     *   et des paramètres supplémentaires qui permettent de spécifier les parents désirés.
     * Une fois les données récupérées, la méthode changeBreadCrumb est appelée
     * pour mettre à jour le ReplaySubject dataBreadCrumb.
     * Si storeDataBreadCrumb est vrai, les données du fil d'Ariane seront stockées dans localStorage
     * et pourront être récupérées ultérieurement. ??? Utile
     *
     * @param {string} moduleCode - The code of the module.
     * @param {string} objectType - The type of the object.
     * @param {number | null} id - The ID of the object.
     * @param {Object} queryParams - Additional query parameters to pass to the API.
     * @param {boolean} storeDataBreadCrumb - Whether to store the breadcrumb data in localStorage.
     */

    // Si l'objet n'est pas de type module et que le breadcrumb ne contient pas le module, on force la récupération du module
    let parentsPath = queryParams['parents_path'] || [];
    parentsPath = Array.isArray(parentsPath) ? parentsPath : [parentsPath];

    if (objectType !== 'module' && !parentsPath.includes('module')) {
      queryParams = {
        ...queryParams,
        parents_path: parentsPath.push('module'),
      };
    }

    this._dataMonitoringObjectService
      .getBreadcrumbs(moduleCode, objectType, id, queryParams)
      .subscribe((data: IBreadCrumb[]) => {
        this.changeBreadCrumb(data, storeDataBreadCrumb);
      });
  }

  changeBreadCrumb(newDataBreadCrumb: IBreadCrumb[], storeDataBreadCrumb: boolean = false) {
    /**
     * Change the breadcrumb data and optionally store it in localStorage
     * to be used later (e.g., after a page refresh).
     *
     * @param {IBreadCrumb[]} newDataBreadCrumb - The new breadcrumb data.
     * @param {boolean} [storeDataBreadCrumb=false] - Whether to store the breadcrumb data in localStorage.
     *   If true, the breadcrumb data will be stored in localStorage and can be retrieved later.
     */
    if (storeDataBreadCrumb) {
      // Store the breadcrumb data in localStorage
      localStorage.setItem('storedDataBreadCrumb', JSON.stringify(newDataBreadCrumb));
    }
    // Update the ReplaySubject dataBreadCrumb with the new breadcrumb data
    this.dataBreadCrumb.next(newDataBreadCrumb);
  }

  changeListOption(newListOption: SelectObject[]) {
    this.dataListOption.next(newListOption);
  }
}
