import { MonitoringObjectService } from '../services/monitoring-object.service';
import { Utils } from '../utils/utils';
import { MonitoringObjectBase } from './monitoring-object-base';
import { Observable, of, forkJoin } from 'rxjs';
import { mergeMap, concatMap } from 'rxjs/operators';

export class MonitoringObject extends MonitoringObjectBase {
  myClass = MonitoringObject;

  constructor(moduleCode: string, objectType: string, id, objService: MonitoringObjectService) {
    super(moduleCode, objectType, id, objService);
  }

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
        return of(this);
      })
    );
  }

  initChildren(childrenData): Observable<any> {
    if (!childrenData) {
      return of(true);
    }

    return forkJoin(
      this.childrenTypes().map((childrenType) => {
        return this.initChildrenOfType(childrenType, childrenData);
      })
    );
  }

  initChildrenOfType(childrenType, childrenData): Observable<any> {
    const childrenDataOfType = childrenData[childrenType];
    if (!childrenDataOfType) {
      return of(true);
    }

    this.children[childrenType] = [];

    if (!(this.id && childrenDataOfType.length)) {
      return of(true);
    }

    const childIdFieldName = this.child0(childrenType).configParam('id_field_name');

    const observables = [];
    for (const childData of childrenDataOfType) {
      const id = childData.properties[childIdFieldName];
      const child = new this.myClass(this.moduleCode, childrenType, id, this._objService);
      child.parents[this.objectType] = this;
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
          .getObject(this.moduleCode, this.objectType, this.id, depth);
      }),
      mergeMap((postData) => {
        // if (!bFromCache) {
        //   this._objService.setCache(this, postData);
        // }
        return this.init(postData);
      })
    );
  }

  post(formValue, dataComplement = {}): Observable<any> {
    return this._objService
      .dataMonitoringObjectService()
      .postObject(this.moduleCode, this.objectType, this.postData(formValue, dataComplement))
      .pipe(
        mergeMap((postData) => {
          this.id = postData['id'];
          this._objService.setCache(this, postData);
          return this.init(postData);
        })
      );
  }

  patch(formValue, dataComplement = {}) {
    return this._objService
      .dataMonitoringObjectService()
      .patchObject(
        this.moduleCode,
        this.objectType,
        this.id,
        this.postData(formValue, dataComplement)
      )
      .pipe(
        mergeMap((postData) => {
          this._objService.setCache(this, postData);
          return this.init(postData);
        })
      );
  }

  delete() {
    this._objService.deleteCache(this);
    return this._objService
      .dataMonitoringObjectService()
      .deleteObject(this.moduleCode, this.objectType, this.id);
  }

  getParents(depth = 0): Observable<any> {
    const promises = {};
    if (!this.parentTypes().length) {
      return of({});
    }
    for (const parentType of this.parentTypes()) {
      promises[parentType] = this.getParent(parentType, depth);
    }
    return forkJoin(promises);
  }

  parent(parentType = null) {
    if (!parentType) {
      parentType = this.parentType();
    }

    const parent = this.parents[parentType];
    if (!parent) {
      return;
    }
    parent.parentsPath = [...this.parentsPath];
    parent.parentsPath.pop();
    return parent;
  }

  /** methodes pour obtenir les parent et enfants de l'object */
  getParent(parentType = null, depth = 0): Observable<any> {
    if (!parentType) {
      parentType = this.parentType();
    }

    let parentOut = null;

    if (parentType != 'module' && !this.parentId(parentType)) {
      return of(null);
    }

    return of(true).pipe(
      mergeMap(() => {
        if (this.parents[parentType]) {
          return of(this.parents[parentType]);
        } else {
          return new this.myClass(
            this.moduleCode,
            parentType,
            this.parentId(parentType),
            this._objService
          ).get(depth);
        }
      }),
      mergeMap((parent) => {
        parentOut = parent;
        this.parents[parent.objectType] = parent;
        return parent.getParents(depth);
      }),
      concatMap((parents) => {
        for (const key of Object.keys(parents)) {
          if (parents[key]) {
            this.parents[key] = parents[key];
          }
        }
        return of(parentOut);
      })
    );
  }

  /** Formulaires  */

  /** formValues: obj -> from */

  formValues(schemaUpdate = {}): Observable<any> {
    const properties = Utils.copy(this.properties);
    const observables = {};
    let schema = {};
    if (Object.keys(schemaUpdate).length == 0) {
      schema = this.schema();
    } else {
      schema = schemaUpdate;
    }

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
        if (this.config['geometry_type']) {
          formValues['geometry'] = this.geometry; // copy???
        }
        return of(formValues);
      })
    );
  }

  /** postData: obj -> from */

  postData(formValue, dataComplement) {
    const propertiesData = {};
    const schema = this.schema();
    for (const attribut_name of Object.keys(schema)) {
      const elem = schema[attribut_name];
      if (!elem.type_widget) {
        continue;
      }
      propertiesData[attribut_name] = this._objService.fromForm(elem, formValue[attribut_name]);
    }

    let postData = {};
    if (Object.keys(dataComplement).length == 0) {
      postData = {
        properties: propertiesData,
        // id_parent: this.parentId
      };
    } else {
      postData = {
        properties: propertiesData,
        dataComplement: dataComplement,
        // id_parent: this.parentId
      };
    }

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

    return Utils.mapArrayToDict(this.childrenTypes(), (childrenType) => {
      return this.child0(childrenType);
    });
  }

  children0Array() {
    if (!this.childrenTypes()) {
      return null;
    }

    return this.childrenTypes().map((childrenType) => {
      return this.child0(childrenType);
    });
  }

  /** list */

  childrenColumnsAndRowsOfType(childrenType, typeDisplay) {
    const child0 = this.child0(childrenType);
    const childrenFieldLabels = child0.fieldLabels();
    const childrenFieldNames = child0.fieldNames(typeDisplay);
    const childrenFieldDefinitons = child0.fieldDefinitions();

    const columns = childrenFieldNames.map((fieldName) => {
      return {
        prop: fieldName,
        name: childrenFieldLabels[fieldName],
        definition: childrenFieldDefinitons[fieldName],
      };
    });

    let rows = [];
    if (this.children[childrenType]) {
      rows = this.children[childrenType].map((child) => {
        const row = Utils.mapArrayToDict(
          childrenFieldNames,
          (fieldName) => child.resolvedProperties[fieldName]
        );
        row['id'] = child.id;
        row['cruved'] = child.cruved;
        return row;
      });
    }

    return {
      columns: columns,
      rows: rows,
    };
  }

  childrenColumnsAndRows(typeDisplay) {
    return Utils.mapArrayToDict(this.childrenTypes(), (childrenType) => {
      return this.childrenColumnsAndRowsOfType(childrenType, typeDisplay);
    });
  }
}
