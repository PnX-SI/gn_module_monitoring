import { Observable, of } from "@librairies/rxjs";
import { concatMap } from "@librairies/rxjs/operators";

import { MonitoringObjectService } from "../services/monitoring-object.service";
import { Utils } from "../utils/utils";

export class MonitoringObjectBase {
  moduleCode: string;
  objectType: string;
  id: number; // id de l'objet

  parentsPath = [];

  userCruved;
  deleted = false;

  idTableLocation;
  properties = {}; // liste des propriétés de type non géométrie
  geometry;

  resolvedProperties = {}; // liste des propriétés de type non géométrie résolues???

  medias; // children ?

  bIsInitialized = false;

  children = {};
  _children0 = {};
  parents = {};
  myClass = MonitoringObjectBase;

  siteId;

  template = {};

  configParams = ["geometry_type"];
  config = {};

  public _objService: MonitoringObjectService;

  constructor(
    moduleCode: string,
    objectType: string,
    id,
    objService: MonitoringObjectService
  ) {
    if (!moduleCode) {
      throw new Error("Monitoring object sans moduleCode");
    }
    this.objectType = objectType;
    this.moduleCode = moduleCode;
    this.id = id;
    this._objService = objService;
  }

  monitoringObjectService() {
    return this._objService;
  }

  toString() {
    return `Object - ${this.moduleCode} ${this.objectType} ${this.id}`;
  }

  initTemplate() {
    this.template["idTableLocation"] = this.configParam("id_table_location");
    this.template["label"] = this.configParam("label");
    this.template["label_list"] =
      this.configParam("label_list") || this.configParam("label") + "s";

    this.template["title"] = this.title();

    this.template["uuid"] = this.paramValue("uuid_field_name");
    this.template["description"] = this.paramValue(
      "description_field_name",
      true
    );

    this.template["fieldLabels"] = this.fieldLabels();
    this.template["fieldNames"] = this.fieldNames("display_properties");
    this.template["fieldDefinitions"] = this.fieldDefinitions();
    this.template["fieldNamesList"] = this.fieldNames("display_list");
  }

  setConfig() {
    for (const configParam of this.configParams) {
      this.config[configParam] = this.configParam(configParam);
    }
  }

  setData(data) {
    this.userCruved = data.cruved;
    this.properties = data.properties;
    this.geometry = data.geometry;
    this.id = this.id || this.properties[this.configParam("id_field_name")];
    this.medias = data.medias;
    this.siteId = data.site_id;
    this.idTableLocation = data.id_table_location;
  }

  idFieldName() {
    return this._objService
      .configService()
      .configModuleObjectParam(
        this.moduleCode,
        this.objectType,
        "id_field_name"
      );
  }

  parentId(parentType = null) {
    if (!parentType) {
      parentType = this.parentType();
    }
    return this.properties[this.parentIdFieldName(parentType)];
  }

  parentIdFieldName(parentType) {
    return !parentType
      ? null
      : this._objService
          .configService()
          .configModuleObjectParam(
            this.moduleCode,
            parentType,
            "id_field_name"
          );
  }

  resolveProperty(elem, val): Observable<any> {
    const configUtil = this._objService.configUtils(elem, this.moduleCode);

    if (elem.type_widget === "date" || (elem.type_util === "date" && val)) {
      val = Utils.formatDate(val);
    }

    if (val && configUtil && elem.type_widget) {
      return this._objService
        .dataUtilsService()
        .getUtil(elem.type_util, val, configUtil.fieldName);
    }
    return of(val);
  }

  setResolvedProperties(): Observable<any> {
    const observables = {};
    const schema = this.schema();
    for (const attribut_name of Object.keys(schema)) {
      observables[attribut_name] = this.resolveProperty(
        schema[attribut_name],
        this.properties[attribut_name]
      );
    }
    return Observable.forkJoin(observables).pipe(
      concatMap((resolvedProperties) => {
        for (const attribut_name of Object.keys(resolvedProperties)) {
          this.resolvedProperties[attribut_name] =
            resolvedProperties[attribut_name];
        }
        return of(true);
      })
    );
  }

  configParam(fieldName) {
    return this._objService
      .configService()
      .configModuleObjectParam(this.moduleCode, this.objectType, fieldName);
  }

  cruved(c = null) {
    const cruved = this.configParam("cruved") || {};
    return c
      ? ![undefined, null].includes(cruved[c])
        ? cruved[c]
        : 1
      : cruved;
  }

  childrenTypes(configParam: string = null): Array<string> {
    let childrenTypes = this.configParam("children_types") || [];

    if (configParam) {
      childrenTypes = childrenTypes.filter((TypeChildren) => {
        return this.child0(TypeChildren).config[configParam];
      });
    }
    return childrenTypes || [];
  }

  uniqueChildrenName() {
    const childrenTypes = this.configParam("children_types") || [];

    if (childrenTypes.length === 1) {
      return this.child0(childrenTypes[0]).template.label_list;
    }
  }

  uniqueChildrenType() {
    const childrenTypes = this.configParam("children_types") || [];

    if (childrenTypes.length === 1) {
      return childrenTypes[0];
    }
  }

  parentTypes() {
    return this.configParam("parent_types");
  }

  parentType() {
    return this.parentsPath && this.parentsPath.length
      ? this.parentsPath[this.parentsPath.length - 1]
      : this.parentTypes().length
      ? this.parentTypes()[0]
      : null;
  }

  child0(childrenType) {
    if (this._children0[childrenType]) {
      return this._children0[childrenType];
    }
    const child0 = new this.myClass(
      this.moduleCode,
      childrenType,
      null,
      this._objService
    );
    child0.parentsPath = [...this.parentsPath];
    child0.parentsPath.push(this.objectType)

    child0.setConfig();
    child0.initTemplate();
    this._children0[childrenType] = child0;
    return this._children0[childrenType];
  }

  childsLabel() {
    return Utils.mapArrayToDict(this.childrenTypes(), (childrenType) => {
      return this.child0(childrenType).configParam("label");
    });
  }

  paramValue(param, bResolved = false) {
    const fieldName = this.configParam(param);
    if (bResolved) {
      return fieldName && this.properties[fieldName];
    } else {
      return fieldName && this.resolvedProperties[fieldName];
    }
  }

  title() {
    const title = this.configParam("label");
    const description = this.paramValue("description_field_name", true);
    return description ? title + " " + description : title;
  }

  schema(typeSchema = "all"): Object {
    return this._objService
      .configService()
      .schema(this.moduleCode, this.objectType, typeSchema);
  }

  change() {
    return this._objService
      .configService()
      .change(this.moduleCode, this.objectType);
  }

  fieldNames(typeDisplay = "") {
    if (["display_properties", "display_list"].includes(typeDisplay)) {
      return this.configParam(typeDisplay);
    }
    if (typeDisplay === "schema") {
      return Object.keys(this.schema());
    }
  }

  /** return dict as {..., attribut_name: label, ...} */
  fieldLabels() {
    const schema = this.schema();
    const fieldLabels = {};
    for (const key of Object.keys(schema)) {
      fieldLabels[key] = schema[key]["attribut_label"];
    }
    return fieldLabels;
  }

  fieldDefinitions() {
    const schema = this.schema();
    const fieldDefinitions = {};
    for (const key of Object.keys(schema)) {
      fieldDefinitions[key] = schema[key]["definition"];
    }
    return fieldDefinitions;
  }

  geoFeature() {
    // patch
    this.resolvedProperties["object_type"] = this.objectType;
    this.resolvedProperties["description"] = this.paramValue(
      "description_field_name",
      true
    );

    return {
      id: this.id,
      object_type: this.objectType,
      type: "Feature",
      geometry: this.geometry,
      properties: this.resolvedProperties,
    };
  }

  isRoot() {
    return !this.parentTypes().length && this.childrenTypes();
  }

  /** navigation */

  navigateToAddChildren(childrenType=null) {
    
    const queryParamsAddChildren = {};
    queryParamsAddChildren[this.idFieldName()] = this.id;
    queryParamsAddChildren["parents_path"] = this.parentsPath.concat(
      this.objectType
    );
    this._objService.navigate(
      "create_object",
      this.moduleCode,
      childrenType || this.uniqueChildrenType(),
      null,
      queryParamsAddChildren,
    );
  }

  navigateToDetail(id = null) {
    this._objService.navigate(
      "object",
      this.moduleCode,
      this.objectType,
      id || this.id,
      {
        parents_path: this.parentsPath
      }
    );
  }

  navigateToParent() {
    // cas module
    if (this.objectType.includes("module")) {
      this.navigateToDetail();

      // autres cas
    } else {
      const parentType = this.parentType();
      this.parentsPath.pop();
      const parent = new this.myClass(
        this.moduleCode,
        parentType,
        null,
        this._objService
      );
      const parentId = this.properties[parent.idFieldName()];
      this._objService.navigate(
        "object",
        this.moduleCode,
        parentType,
        parentId,
        {
          parents_path: this.parentsPath,
        }
      );
    }
  }
}
