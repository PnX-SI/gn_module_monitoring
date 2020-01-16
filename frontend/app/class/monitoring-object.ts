import { Observable, of, forkJoin } from "@librairies/rxjs";
import { mergeMap, concatMap } from "@librairies/rxjs/operators";


import { MonitoringObjectService } from "../services/monitoring-object.service";
import { Utils } from "../utils/utils";

import { MonitoringObjectBase } from "./monitoring-object-base";

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
    //set data et get children
    this.setConfig();
    this.setData(objData);

    let observables = [this.resolveProperties()];

    if (this.id && this.childrenTypes().length) {
      observables.push(this.initChildren(objData.children));
    }

    return forkJoin(observables).pipe(
      concatMap(() => {
        // this.bIsInitialized = true;
        return of(true);
      })
    );
  }

  initChildren(childrenData): Observable<any> {
    if (!(this.id && childrenData)) {
      return of(true);
    }

    return forkJoin(
      this.childrenTypes().map(childrenType => {
        return this.initChildrenOfType(childrenType, childrenData);
      })
    );
  }

  initChildrenOfType(childrenType, childrenData): Observable<any> {
    let childrenDataOfType = childrenData[childrenType];
    // if (!(childrenDataOfType && childrenDataOfType.length)) {
    if (!(childrenDataOfType)) {
      return of(true);
    }

    this.children[childrenType] = [];
    console.log(childrenType)
    let childIdFieldName = this.child0(childrenType).configParam(
      "id_field_name"
    );
    if (childrenDataOfType.length == 0) {
      return of(true);
    }
    let observables = [];
    for (let childData of childrenDataOfType) {
      let id = childData.properties[childIdFieldName];
      let child = new this.myClass(
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
    return this._objService
      .dataMonitoringObjectService()
      .getObject(this.modulePath, this.objectType, this.id, depth)
      .pipe(
        mergeMap(postData => {
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
          return this.init(postData);
        })
      );
  }

  delete() {
    return this._objService
      .dataMonitoringObjectService()
      .deleteObject(this.modulePath, this.objectType, this.id);
  }

  /** methodes pour obtenir les parent et enfants de l'object */

  getParent(depth = 0): Observable<any> {
    if (
      !this.parentType() ||
      this.parent ||
      !(this.parentId || this.parentType().includes("module"))
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
    let properties = Utils.copy(this.properties);
    let schema = this.schema();
    let observables = schema
      .filter(elem => elem.type_widget)
      .map(elem => {
        this.setElemValueFromOtherObject(elem);
        return this._objService.toForm(elem, properties[elem.attribut_name]);
      });

    return forkJoin(observables).pipe(
      concatMap(formValuesArray => {
        let formValues = {};
        schema
          .filter(elem => elem.type_widget)
          .forEach((elem, index) => {
            formValues[elem.attribut_name] = formValuesArray[index];
          });
        //geometry
        if (this.config["geometry_type"]) {
          formValues["geometry"] = this.geometry; // copy???
        }
        return of(formValues);
      })
    );
  }

  /** postData: obj -> from */

  postData(formValue) {
    let propertiesData = {};
    this.schema().forEach(elem => {
      propertiesData[elem.attribut_name] = this._objService.fromForm(
        elem,
        formValue[elem.attribut_name]
      );
    });

    let postData = {
      properties: propertiesData,
      id_parent: this.parentId
    };

    if (this.config["geometry_type"]) {
      postData["geometry"] = formValue["geometry"];
      postData["type"] = "Feature";
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
    let child0 = this.child0(childrenType);
    let childrenFieldLabels = child0.fieldLabels();
    let childrenFieldNames = child0.fieldNames(typeDisplay);

    let columns = childrenFieldNames.map(fieldName => {
      return { prop: fieldName, name: childrenFieldLabels[fieldName] };
    });

    let rows = [];
    if (this.children[childrenType]) {
      rows = this.children[childrenType].map(child => {
        let row = Utils.mapArrayToDict(
          childrenFieldNames,
          fieldName => child.resolvedProperties[fieldName]
        );
        row["id"] = child.id;
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

  /** Geometry :  sibbling, children, parent TODO*/

  sibblingGeometries() {
    if (
      !(this.config["geometry_type"] && this.parent && this.parent.children)
    ) {
      return null;
    }

    let sibblingGeometries = this.parent.childrenGeometriesOfType(
      this.objectType
    );

    if (!sibblingGeometries) {
      return null;
    }

    let features = sibblingGeometries["features"].filter(geom => {
      return geom.id != this.id;
    });

    sibblingGeometries.features = features;

    return sibblingGeometries;
  }

  childrenGeometriesOfType(childrenType) {
    let childrenWithGeom = this.children[childrenType];
    if (!childrenWithGeom) {
      return null;
    }

    let features = childrenWithGeom.map(child => {
      return child.geoFeature();
    });

    return {
      type: "FeatureCollection",
      features: features
    };
  }

  childrenGeometries() {
    return Utils.mapArrayToDict(
      this.childrenTypes("geometry_type"),
      childrenType => {
        return this.childrenGeometriesOfType(childrenType);
      }
    );
  }

}
