import { Observable, of, forkJoin } from '@librairies/rxjs';
import { mergeMap, concatMap } from '@librairies/rxjs/operators';


import { MonitoringObjectService } from '../services/monitoring-object.service';
import { Utils } from '../utils/utils';

import { MonitoringObjectBase } from './monitoring-object-base';
//======================================================================================
//======================================================================================

export class MonitoringObject extends MonitoringObjectBase {
  parent: MonitoringObject;
  myClass = MonitoringObject;
//======================================================================================
  constructor(
    modulePath: string,
    objectType: string,
    id,
    objService: MonitoringObjectService
  ) {
    super(modulePath, objectType, id, objService);
  }
//======================================================================================
  /** Initialisation de l'object à partir des données du serveur */

  init(objData): Observable<any> {
    
    // set data et get children
    this.setConfig();
    this.setData(objData);

    const observables = [this.setResolvedProperties()];

    if (this.childrenTypes().length && objData) {
      observables.push(this.initChildren(objData.children));
    }

    return forkJoin(observables).pipe(
      concatMap(() => {
        return of(true);
      })
    );
  }
//======================================================================================
  initChildren(childrenData): Observable<any> {
    if (!childrenData) {
      return of(true);
    }

    return forkJoin(
      this.childrenTypes().map(childrenType => {
        return this.initChildrenOfType(childrenType, childrenData);
      })
    );
  }
//======================================================================================
  initChildrenOfType(childrenType, childrenData): Observable<any> {
    const childrenDataOfType = childrenData[childrenType];

    console.log("childrenType: "+childrenType);
    console.log("childrenDataOfType");    console.log(childrenDataOfType);

    if (!(childrenDataOfType)) {
      return of(true);
    }

    this.children[childrenType] = [];

    if (!(this.id && childrenDataOfType.length)) {
      return of(true);
    }

    const childIdFieldName = this.child0(childrenType).configParam(
      'id_field_name'
    );

    const observables = [];
    for (const childData of childrenDataOfType) {
      
     
      const id = childData.properties[childIdFieldName];
      const child = new this.myClass(
        this.modulePath,
        childrenType,
        id,
        this._objService
      );
      
      child.parentId = this.id;
      child.parent = this;
      
      this.children[childrenType].push(child);
      observables.push(child.init(childData));
    }
    return forkJoin(observables);
  }
//======================================================================================
  /** Methodes get post patch delete */

  get(depth): Observable<any> {
    let bFromCache = false;
 

    return of(true).pipe(
      mergeMap(() => {
        const postData = this._objService.getFromCache(this);

        if (postData) {
          bFromCache = true;
          return of(postData);
          
        }
        


        return this._objService
          .dataMonitoringObjectService()
          .getObject(this.modulePath, this.objectType, this.id, depth);
      }),
      
      mergeMap(postData => {
        if (!bFromCache) {
          this._objService.setCache(this, postData);
        }

        return this.init(postData);
      })
    );
  }
//======================================================================================
  post(formValue): Observable<any> {
    return this._objService
      .dataMonitoringObjectService()
      .postObject(this.modulePath, this.objectType, this.postData(formValue))
      .pipe(
        mergeMap(postData => {
          this.id = postData['id'];
          this._objService.setCache(this, postData);
          return this.init(postData);
        })
      );
  }
//======================================================================================
  patch(formValue) {
    return this._objService
      .dataMonitoringObjectService()
      .patchObject(
        this.modulePath,
        this.objectType,
        this.id,
        this.postData(formValue)
      )
      .pipe(
        mergeMap(postData => {
          this._objService.setCache(this, postData);
          return this.init(postData);
        })
      );
  }
//======================================================================================
  delete() {
    this._objService.deleteCache(this);
    return this._objService
      .dataMonitoringObjectService()
      .deleteObject(this.modulePath, this.objectType, this.id);
  }
//======================================================================================
  /** methodes pour obtenir les parent et enfants de l'object */

  getParent(depth = 0): Observable<any> {
    if (
      !this.parentType() ||
      this.parent ||
      !(this.parentId || this.parentType().includes('module'))
    ) {
      return of(true);
    }

    this.parent = new this.myClass(
      this.modulePath,
      this.parentType(),
      this.parentId,
      this._objService
    );
    return this.parent.get(depth);
  }

  /** Formulaires  */

  /** formValues: obj -> from */
//======================================================================================
  formValues(): Observable<any> {
    const properties = Utils.copy(this.properties);
    const observables = {};
    const schema = this.schema();
    for (const attribut_name of Object.keys(schema)) {
      const elem = schema[attribut_name];
      if (!elem.type_widget) {
        continue;
      }
        observables[attribut_name] = this._objService.toForm(elem, properties[attribut_name]);
    }

    return forkJoin(observables).pipe(
      concatMap(formValues_in => {
        const formValues = Utils.copy(formValues_in);
        // geometry
        if (this.config['geometry_type']) {
          formValues['geometry'] = this.geometry; // copy???
        }
        return of(formValues);
      })
    );
  }

  /** postData: obj -> from */
//======================================================================================
  postData(formValue) {
    const propertiesData = {};
    const schema = this.schema();
    for (const attribut_name of Object.keys(schema)) {
      const elem = schema[attribut_name];
      if (!elem.type_widget) {
        continue;
      }
      propertiesData[elem.attribut_name] = this._objService
        .fromForm(elem, formValue[elem.attribut_name]);
    }

    const postData = {
      properties: propertiesData,
      id_parent: this.parentId
    };

    if (this.config['geometry_type']) {
      postData['geometry'] = formValue['geometry'];
      postData['type'] = 'Feature';
    }
    return postData;
  }
//======================================================================================
  /** child0 et children0 pour les templates html */

  children0() {
    if (!this.childrenTypes()) {
      return null;
    }

    return Utils.mapArrayToDict(this.childrenTypes(), childrenType => {
      return this.child0(childrenType);
    });
  }
//======================================================================================
  children0Array() {
    if (!this.childrenTypes()) {
      return null;
    }

    return this.childrenTypes().map(childrenType => {
      return this.child0(childrenType);
    });
  }


  /** list */
//======================================================================================
  childrenColumnsAndRowsOfType(childrenType, typeDisplay) {
    console.log("===========/home/geonatureadmin/geonature/external_modules/monitorings/frontend/app/class/monitoring-object.ts:"  );
    console.log("childrenColumnsAndRowsOfType: childrentype: "+childrenType);
    const child0 = this.child0(childrenType);
    const childrenFieldLabels = child0.fieldLabels();
    const childrenFieldNames = child0.fieldNames(typeDisplay);
    const childrenFieldDefinitons = child0.fieldDefinitions();
    
    //-------------------------------------column
    const columns = childrenFieldNames.map(fieldName => {
      return {
        prop: fieldName,
        name: childrenFieldLabels[fieldName],
        definition: childrenFieldDefinitons[fieldName],
      };
    });
    console.log("columns");  //--------------------
    console.log(columns);  //--------------------




    
//-------------------------------------ROW
    let rows = [];
    
    console.log(this.children);//-----------------------
    if (this.children[childrenType]) {
        rows = this.children[childrenType].map(child => {
        const row = Utils.mapArrayToDict(
          childrenFieldNames,
          fieldName => child.resolvedProperties[fieldName]
        );
        row['id'] = child.id;
        return row;
      });
    }
   
    console.log("rows");  //--------------------
    console.log(rows);  //--------------------
    return {
      columns: columns,
      rows: rows
    };
  }

  childrenColumnsAndRows(typeDisplay) {
    return Utils.mapArrayToDict(this.childrenTypes(), childrenType => {
      return this.childrenColumnsAndRowsOfType(childrenType, typeDisplay);
    });
  }

}
