import { MonitoringObjectService } from '../services/monitoring-object.service';
import { Utils } from '../utils/utils';
import { Observable, of } from 'rxjs';
import { forkJoin } from 'rxjs';
import { concatMap } from 'rxjs/operators';
export class MonitoringObjectBase {
  moduleCode: string;
  objectType: string;
  id: number; // id de l'objet
  cruved: Object;
  parentsPath = [];
  is_geom_from_child: boolean;
  userCruvedObject;
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
  template_specific = {};

  // configParams = ["geometry_type", "chained"];
  config = {};

  public _objService: MonitoringObjectService;

  constructor(moduleCode: string, objectType: string, id, objService: MonitoringObjectService) {
    if (!moduleCode) {
      throw new Error('Monitoring object sans moduleCode');
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

  testPremiereLettreVoyelle(s) {
    return s && s[0] && 'aeéiouy'.includes(s[0].toLowerCase());
  }

  labelArtDef() {
    return (
      (this.testPremiereLettreVoyelle(this.configParam('label'))
        ? "l'"
        : this.configParam('genre') == 'F'
          ? 'la '
          : 'le ') + this.configParam('label').toLowerCase()
    );
  }

  labelDu() {
    const labelDu =
      (this.testPremiereLettreVoyelle(this.configParam('label'))
        ? "de l'"
        : this.configParam('genre') == 'F'
          ? 'de la '
          : 'du ') + this.configParam('label').toLowerCase();
    return labelDu;
  }

  labelArtUndef(newObj = false) {
    const strNew = (newObj && this.configParam('genre') == 'F' ? 'nouvelle ' : 'nouveau ') || '';

    return (
      (this.configParam('genre') == 'F' ? `une ` : `un `) +
      strNew +
      this.configParam('label').toLowerCase()
    );
  }

  initTemplate() {
    this.template['export_pdf'] = this.configParam('export_pdf');
    this.template['export_csv'] = this.configParam('export_csv');
    this.template['color'] = this.configParam('color');
    this.template['idTableLocation'] = this.configParam('id_table_location');
    this.template['label'] = this.configParam('label');
    this.template['label_art_def'] = this.labelArtDef();
    this.template['label_art_undef'] = this.labelArtUndef();
    this.template['label_art_undef_new'] = this.labelArtUndef(true);
    this.template['label_list'] = this.configParam('label_list') || this.configParam('label') + 's';

    // this.template["title"] = this.title();

    this.template['uuid'] = this.paramValue('uuid_field_name');
    this.template['description'] = this.description();

    this.template['fieldLabels'] = this.fieldLabels();
    this.template['fieldNames'] = this.fieldNames('display_properties');
    this.template['fieldDefinitions'] = this.fieldDefinitions();
    this.template['fieldNamesList'] = this.fieldNames('display_list');
  }

  setConfig() {
    this.config = this._objService
      .configService()
      .configModuleObject(this.moduleCode, this.objectType);
    // for (const configParam of this.configParams) {
    //   this.config[configParam] = this.configParam(configParam);
    // }
  }

  setData(data) {
    this.userCruvedObject = data.cruved_objects;
    this.properties = data.properties || {};
    this.geometry = data.geometry;
    this.id = this.id || (this.properties && this.properties[this.configParam('id_field_name')]);
    this.medias = data.medias;
    if (data.site_id) {
      this.siteId = data.site_id;
    }
    this.idTableLocation = data.id_table_location;
    this.cruved = data.cruved;
  }

  idFieldName() {
    return this._objService
      .configService()
      .configModuleObjectParam(this.moduleCode, this.objectType, 'id_field_name');
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
          .configModuleObjectParam(this.moduleCode, parentType, 'id_field_name');
  }

  resolveProperty(elem, val): Observable<any> {
    if (elem.type_widget === 'date' || (elem.type_util === 'date' && val)) {
      val = Utils.formatDate(val);
    }

    const fieldName = this._objService.configUtils(elem, this.moduleCode);
    if (val && fieldName && elem.type_widget) {
      console.log(elem.type_util, val, fieldName, elem.value_field_name);
      return this._objService
        .dataUtilsService()
        .getUtil(elem.type_util, val, fieldName, elem.value_field_name);
    }
    return of(val);
  }

  setResolvedProperties(): Observable<any> {
    const observables = {};
    const schema = this.schema();

    if (Object.keys(this.template_specific).length > 0) {
      Object.assign(schema, this.template_specific['schema']);
    }
    for (const attribut_name of Object.keys(schema)) {
      observables[attribut_name] = this.resolveProperty(
        schema[attribut_name],
        this.properties[attribut_name]
      );
    }
    return forkJoin(observables).pipe(
      concatMap((resolvedProperties) => {
        for (const attribut_name of Object.keys(resolvedProperties)) {
          this.resolvedProperties[attribut_name] = resolvedProperties[attribut_name];
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

  childrenTypes(configParam: string = null): Array<string> {
    let childrenTypes = this.configParam('children_types') || [];

    if (configParam) {
      childrenTypes = childrenTypes.filter((TypeChildren) => {
        return this.child0(TypeChildren).config[configParam];
      });
    }
    return childrenTypes || [];
  }

  uniqueChildrenName() {
    const childrenTypes = this.configParam('children_types') || [];

    if (childrenTypes.length === 1) {
      return this.child0(childrenTypes[0]).template.label_list;
    }
  }

  hasChildren() {
    return !!this.configParam('children_types');
  }

  uniqueChildrenType() {
    const childrenTypes = this.configParam('children_types') || [];

    if (childrenTypes.length === 1) {
      return childrenTypes[0];
    }
  }

  parentTypes() {
    return this.configParam('parent_types');
  }

  parentType() {
    return this.parentsPath && this.parentsPath.length
      ? this.parentsPath[this.parentsPath.length - 1]
      : this.parentTypes().length
        ? this.parentTypes()[0]
        : null;
  }

  child0(childrenType) {
    if (!this.childrenTypes().length) {
      return;
    }
    if (this._children0[childrenType]) {
      return this._children0[childrenType];
    }
    const child0 = new this.myClass(
      this.moduleCode,
      childrenType || this.uniqueChildrenType(),
      null,
      this._objService
    );
    child0.parentsPath = [...this.parentsPath];
    child0.parentsPath.push(this.objectType);

    child0.setConfig();
    child0.initTemplate();
    this._children0[childrenType] = child0;
    return this._children0[childrenType];
  }

  childsLabel() {
    return Utils.mapArrayToDict(this.childrenTypes(), (childrenType) => {
      return this.child0(childrenType).configParam('label');
    });
  }

  paramValue(param, bResolved = false) {
    const fieldName = this.configParam(param);
    if (!bResolved) {
      return fieldName && this.properties[fieldName];
    } else {
      return fieldName && this.resolvedProperties[fieldName];
    }
  }

  title(bEdit = false) {
    const description = this.description();
    const text = bEdit
      ? this.id
        ? `Modification ${this.labelDu()} ${description}`
        : `Création d'${this.labelArtUndef(true)}`
      : `Détails ${this.labelDu()} ${description}`;

    return text.trim();
  }

  description() {
    let description = this.paramValue('description_field_name', true);
    return description;
  }

  titleHTML(bEdit = false) {
    let description = this.description();
    description = description ? `<span class="obj-description">${description}</span>` : '';
    const text = bEdit
      ? this.id
        ? `Modification ${this.labelDu()} ${description}`
        : `Création d'${this.labelArtUndef(true)}`
      : `Détails ${this.labelDu()} ${description}`;

    return text.trim();
  }

  schema(typeSchema = 'all'): Object {
    return this._objService.configService().schema(this.moduleCode, this.objectType, typeSchema);
  }

  change() {
    return this._objService.configService().change(this.moduleCode, this.objectType);
  }

  fieldNames(typeDisplay = '') {
    if (['display_properties', 'display_list'].includes(typeDisplay)) {
      return this.configParam(typeDisplay);
    }
    if (typeDisplay === 'schema') {
      return Object.keys(this.schema());
    }
  }

  /** return dict as {..., attribut_name: label, ...} */
  fieldLabels() {
    const schema = this.schema();
    const fieldLabels = {};
    for (const key of Object.keys(schema)) {
      fieldLabels[key] = schema[key]['attribut_label'];
    }
    return fieldLabels;
  }

  fieldDefinitions() {
    const schema = this.schema();
    const fieldDefinitions = {};
    for (const key of Object.keys(schema)) {
      fieldDefinitions[key] = schema[key]['definition'];
    }
    return fieldDefinitions;
  }

  geoFeature() {
    // patch
    this.resolvedProperties['object_type'] = this.objectType;
    this.resolvedProperties['description'] = this.description();

    return {
      id: this.id,
      object_type: this.objectType,
      type: 'Feature',
      geometry: this.geometry,
      properties: this.resolvedProperties,
    };
  }

  isRoot() {
    return !this.parentTypes().length && this.childrenTypes();
  }

  /** navigation */

  navigateToAddChildren(childrenType = null, id = null) {
    const queryParamsAddChildren = {};
    queryParamsAddChildren[this.idFieldName()] = this.id || id;
    queryParamsAddChildren['parents_path'] = this.parentsPath.concat(this.objectType);
    this._objService.navigate(
      'create_object',
      this.moduleCode,
      childrenType || this.uniqueChildrenType(),
      null,
      queryParamsAddChildren
    );
  }

  navigateToDetail(id = null, toEdit = false) {
    this._objService.navigate('object', this.moduleCode, this.objectType, id || this.id, {
      parents_path: this.parentsPath,
      edit: toEdit,
    });
  }

  navigateToParent() {
    // cas module
    if (this.objectType.includes('module')) {
      this.navigateToDetail();

      // autres cas
    } else {
      const parentType = this.parentType();
      this.parentsPath.pop();
      const parent = new this.myClass(this.moduleCode, parentType, null, this._objService);
      const parentId = this.properties[parent.idFieldName()];
      this._objService.navigate('object', this.moduleCode, parentType, parentId, {
        parents_path: this.parentsPath,
      });
    }
  }
}
