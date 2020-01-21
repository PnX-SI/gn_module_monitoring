import { Observable, of, forkJoin } from '@librairies/rxjs';
import { mergeMap, concatMap } from '@librairies/rxjs/operators';


import { MonitoringObjectService } from '../services/monitoring-object.service';
import { Utils } from '../utils/utils';

import { MonitoringObjectBase } from './monitoring-object-base';

export class MonitoringObject extends MonitoringObjectBase {
  parent: MonitoringObject;
  myClass = MonitoringObject;

  constructor(
    modulePath: string,
    objectType: string,
    id,
    objService: MonitoringObjectService
  ) {
    super(modulePath, objectType, id, objService);
  }

  /** Initialisation de l'object à partir des données du serveur */

  init(objData): Observable<any> {
    // set data et get children
    this.setConfig();
    this.setData(objData);

    const observables = [this.resolveProperties()];

    if (this.childrenTypes().length && objData) {
      observables.push(this.initChildren(objData.children));
    }

    return forkJoin(observables).pipe(
      concatMap(() => {
        return of(true);
      })
    );
  }

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

  initChildrenOfType(childrenType, childrenData): Observable<any> {
    const childrenDataOfType = childrenData[childrenType];
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

  post(formValue): Observable<any> {
    return this._objService
      .dataMonitoringObjectService()
      .postObject(this.modulePath, this.objectType, this.postData(formValue))
      .pipe(
        mergeMap(postData => {
          this._objService.setCache(this, postData);
          return this.init(postData);
        })
      );
  }

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

  delete() {
    this._objService.deleteCache(this);
    return this._objService
      .dataMonitoringObjectService()
      .deleteObject(this.modulePath, this.objectType, this.id);
  }

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

  formValues(): Observable<any> {
    const properties = Utils.copy(this.properties);
    const schema = this.schema();
    const observables = schema
      .filter(elem => elem.type_widget)
      .map(elem => {
        return this._objService.toForm(elem, properties[elem.attribut_name]);
      });

    return forkJoin(observables).pipe(
      concatMap(formValuesArray => {
        const formValues = {};
        schema
          .filter(elem => elem.type_widget)
          .forEach((elem, index) => {
            formValues[elem.attribut_name] = formValuesArray[index];
          });
        // geometry
        if (this.config['geometry_type']) {
          formValues['geometry'] = this.geometry; // copy???
        }
        return of(formValues);
      })
    );
  }

  /** postData: obj -> from */

  postData(formValue) {
    const propertiesData = {};
    this.schema().forEach(elem => {
      propertiesData[elem.attribut_name] = this._objService.fromForm(
        elem,
        formValue[elem.attribut_name]
      );
    });

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

  /** child0 et children0 pour les templates html */

  children0() {
    if (!this.childrenTypes()) {
      return null;
    }

    return Utils.mapArrayToDict(this.childrenTypes(), childrenType => {
      return this.child0(childrenType);
    });
  }

  children0Array() {
    if (!this.childrenTypes()) {
      return null;
    }

    return this.childrenTypes().map(childrenType => {
      return this.child0(childrenType);
    });
  }


  /** list */

  childrenColumnsAndRowsOfType(childrenType, typeDisplay) {
    const child0 = this.child0(childrenType);
    const childrenFieldLabels = child0.fieldLabels();
    const childrenFieldNames = child0.fieldNames(typeDisplay);

    const columns = childrenFieldNames.map(fieldName => {
      return {
        prop: fieldName,
        name: childrenFieldLabels[fieldName]
      };
    });

    let rows = [];
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
