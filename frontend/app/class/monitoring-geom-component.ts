import { inject, OnInit, Directive } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '@geonature/components/auth/auth.service';
import { Subscription } from 'rxjs';
import { IdataTableObjData } from '../interfaces/geom';
import { PermissionService } from '../services/permission.service';
import { TemplateData } from '../interfaces/template';
import { ConfigServiceG } from '../services/config-g.service';
import { JsonData } from '../types/jsondata';
import { FormGroup, FormBuilder } from '@angular/forms';
import { Popup } from '../utils/popup';
import { FormService } from '../services/form.service';

const LIMIT = 10;

type callbackFunction = (pageNumber: number, filters: JsonData, tabObj: string) => void;
@Directive()
export class MonitoringGeomComponent implements OnInit {
  protected getAllItemsCallback: callbackFunction;
  protected limit = LIMIT;
  public filters = {};
  public baseFilters = {};

  public moduleConfig: any;
  public moduleCode: string;
  public parentPath: string[] = [];
  public queryParams: {} = {};
  public checkEditParam: boolean = false;
  public currentUser;

  public objectType: string;
  public allowedObjectTypes: string[] = [];

  public form: FormGroup;

  public dataId: number;
  public objectData: any;
  public objectDataResolved: any;

  protected bEdit: boolean = false;
  protected currentEditModeSubscription: Subscription;

  public dataTableObjData: IdataTableObjData;
  public dataTableConfig: {}[] = [];
  public templateData: TemplateData = {
    fieldNames: [],
    fieldLabels: {},
    fieldDefinitions: {},
    childType: [],
    exportPDF: {},
    exportCSV: {},
  };
  public templateSpecificData: TemplateData | {} = {};

  protected _configServiceG: ConfigServiceG;

  constructor(
    public _permissionService: PermissionService,
    public _popup: Popup,
    public _formService: FormService,
    protected _Activatedroute: ActivatedRoute,
    protected _formBuilder: FormBuilder,
    protected _auth: AuthService,
    protected router: Router
  ) {
    this._configServiceG = inject(ConfigServiceG);
  }

  ngOnInit() {
    // Récupération de la configuration du module
    this.moduleCode = this._configServiceG.moduleCode();
    this.moduleConfig = this._configServiceG.config();
    this.currentUser = this._auth.getCurrentUser();

    // Récupération des paramètres de la route
    this.dataId = this._Activatedroute.snapshot.params.id;
    this.checkEditParam = JSON.parse(this._Activatedroute.snapshot.queryParams?.edit || 'false');
    this.parentPath = this._Activatedroute.snapshot.queryParamMap.getAll('parents_path');
    this.queryParams = this._Activatedroute.snapshot.queryParams;

    // Initialisation des formulaires et templates
    this._permissionService.setPermissionMonitorings(this.moduleCode);
    this.form = this._formBuilder.group({});
    this.setTemplateData(this.objectType);

    // Initialisation de la config du datatable
    this.setDataTableConfig();

    // Passage en mode édition si paramètre 'edit' est true
    if (this.checkEditParam === true) {
      this.bEdit = true;
      this._formService.changeCurrentEditMode(this.bEdit);
    }

    this.currentEditModeSubscription = this._formService.currentEditMode.subscribe(
      (value: boolean) => {
        // Permet d'identifier si l'objet est passé en mode édition
        // si c'est le cas, on refresh les données de l'objet
        this.onbEditChange(value);
        this.bEdit = value;
      }
    );
  }

  onbEditChange(event: boolean) {
    console.log('Not implemented');
  }

  setPage({ page, filters, tabObj = '' }) {
    this.filters = { ...this.baseFilters, ...filters };
    this.getAllItemsCallback(page.offset + 1, this.filters, tabObj);
  }

  setSort({ filters, tabObj = '' }) {
    this.filters = { ...this.baseFilters, ...filters };
    const pageNumber = 1;
    this.getAllItemsCallback(pageNumber, this.filters, tabObj);
  }

  setFilter({ filters, tabObj = '' }) {
    this.filters = { ...this.baseFilters, ...filters };
    this.getAllItemsCallback(1, this.filters, tabObj);
  }
  navigateToAddChildren($event) {
    const row = $event;
    if (row) {
      row['id'] = row[row.pk];
      const id_base_site = row?.id_base_site;
      const routeParams = this._Activatedroute.snapshot.queryParams;
      let queryParams: any = {
        parents_path: [...routeParams['parents_path'], this.objectType],
        id_base_site: id_base_site,
      };
      queryParams[row.pk] = row[row.pk];

      this.router.navigate(
        [`/monitorings/object/${this.moduleCode}/`, row['object_type'], 'create'],
        {
          queryParams: queryParams,
        }
      );
    }
  }

  setDataTableConfig() {
    /**
     * Initialisation de la configuration pour ngx-datatable
     *
     * @param {any} data data to set the data table config and data
     * @returns {void}
     */
    const dataTableTypes = this._configServiceG.getChildsByObjectType(this.objectType);
    let dataTableConfig = [];

    for (const dataType of dataTableTypes) {
      let objTypeChild = this._configServiceG.getChildsByObjectType(dataType)[0];
      const objType = `${dataType}`;
      if (!this.allowedObjectTypes.includes(objType)) {
        continue;
      }
      const config = this._configServiceG.config()[objType];

      let canCreateChild = this._permissionService.modulePermission[objTypeChild]?.C > 0 || false;

      if (config['children_types'].length == 0) {
        // Si l'objet n'a pas d'enfant
        canCreateChild = false;
        objTypeChild = null;
      }
      if (this.moduleCode == 'generic' && objTypeChild == 'visit') {
        // Pour le module généric les permissions des visites sont toujours vrai
        //  car ce sont les sous modules qui vont déterminer les permissions
        canCreateChild = true;
      }
      const fieldNamesList = config['display_list'];
      let colNameObj: { [index: string]: any } = {};
      const labelList = config['label_list'];
      for (const key of fieldNamesList) {
        colNameObj[key] = (config['fields'][key] || [])['attribut_label'];
      }
      let currentDataTableConfig = {
        labelList: labelList,
        description_field_name: config['description_field_name'],
        childType: objTypeChild,
        sorts:
          'sorts' in config
            ? {
                sort_dir: config.sorts[0]['dir'] || 'asc',
                sort: config.sorts[0]['prop'],
              }
            : {},
        colNameObj: colNameObj,
        objectType: objType,
        moduleCode: this.moduleCode,
        canCreateObj: this._permissionService.modulePermission[objType]?.C > 0 || false,
        canCreateChild: canCreateChild,
        defaultFilters: config?.filters || {},
      };
      dataTableConfig.push(currentDataTableConfig);
    }
    this.dataTableConfig = dataTableConfig;
  }

  setDataTableObjData(
    data: {
      [key: string]: {
        data: { items: any[]; count: number; limit: number; page: number };
        objType: string;
      };
    },
    moduleCode: any,
    allowedObjectType: string[] = []
  ) {
    /**
     * Initialisation des données et de leur configuration pour ngx-datatable
     *
     * @param {any} data data to set the data table config and data
     * @returns {void}
     */

    const dataTableObjData: IdataTableObjData = {} as IdataTableObjData;

    for (const dataType in data) {
      const objType = data[dataType].objType;
      if (!allowedObjectType.includes(objType)) {
        continue;
      }
      const config = this._configServiceG.config()[objType];

      const fieldNamesList = config['display_list'];
      let colNameObj: { [index: string]: any } = {};
      for (const key of fieldNamesList) {
        colNameObj[key] = (config['fields'][key] || [])['attribut_label'];
      }
      dataTableObjData[objType] = {
        columns: colNameObj,
        rows: data[dataType].data.items,
        page: {
          count: data[dataType].data.count,
          limit: data[dataType].data.limit,
          page: data[dataType].data.page - 1,
          total: data[dataType].data.count,
        },
      };
    }
    this.dataTableObjData = dataTableObjData;
  }

  fetchFieldsProperty(fields: any, property: string) {
    let fieldLabels = {};
    for (const [field_name, field_config] of Object.entries(fields)) {
      fieldLabels[field_name] = field_config[property]; // Valeur par défaut si attribut_label n'existe pas
    }
    return fieldLabels;
  }

  setTemplateData(objectType: string) {
    /**
     * Initialisation des données de configuration pour monitoring-properties-template
     *
     * @param {any}
     * configService service de configuration
     * objectType type d'objet
     * @returns {void}
     */
    const config = this._configServiceG.config()[objectType];
    this.templateData.fieldNames = config['display_properties'];
    this.templateData.childType = config['children_type'];
    this.templateData.exportPDF = config?.export_pdf;
    this.templateData.exportCSV = this._configServiceG.config()['module']?.export_csv;

    // Pas beau
    this.templateData.fieldNames.forEach((field_name) => {
      this.templateData.fieldLabels[field_name] = config.fields[field_name]?.attribut_label;
      this.templateData.fieldDefinitions[field_name] = config.fields[field_name]?.definition;
    });
    return this.templateData;
  }

  setTemplateSpecificData(types_site: { config: { specific: any } }[]) {
    let schemaSpecificType = {};
    let keyHtmlToPop = '';

    for (let type_site of types_site) {
      if (type_site.config && 'specific' in type_site.config) {
        const fields = type_site['config']['specific'];
        // Exclusion des propriétés de type html (TODO hidden ??)
        for (const field_name in fields) {
          const field = fields[field_name];
          if ('type_widget' in field && field['type_widget'] == 'html') {
            keyHtmlToPop = field;
          }
        }
        const { [keyHtmlToPop]: _, ...specificObjWithoutHtml } = type_site['config']['specific'];

        schemaSpecificType = Object.assign(schemaSpecificType, specificObjWithoutHtml);
      }
    }
    this.templateSpecificData = {
      fieldNames: Object.keys(schemaSpecificType),
      fieldLabels: this.fetchFieldsProperty(schemaSpecificType, 'attribut_label'),
      fieldDefinitions: this.fetchFieldsProperty(schemaSpecificType, 'definition'),
      childType: [],
      exportCSV: [],
      exportPDF: [],
    };
    return this.templateSpecificData;
  }

  onEachFeatureSite() {
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(this._configServiceG.moduleCode(), feature, {});
      layer.bindPopup(popup);
    };
  }

  ngOnDestroy() {
    this.currentEditModeSubscription.unsubscribe();
  }
}
