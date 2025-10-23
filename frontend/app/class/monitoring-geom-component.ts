import { IdataTableObjData } from '../interfaces/geom';
import { PermissionService } from '../services/permission.service';
import { TemplateData } from '../interfaces/template';
import { ConfigServiceG } from '../services/config-g.service';
import { JsonData } from '../types/jsondata';
import { inject } from '@angular/core';

const LIMIT = 10;

type callbackFunction = (pageNumber: number, filters: JsonData, tabObj: string) => void;

export class MonitoringGeomComponent {
  protected getAllItemsCallback: callbackFunction;
  protected limit = LIMIT;
  public filters = {};
  public baseFilters = {};

  public dataTableObjData: IdataTableObjData;
  public dataTableConfig: {}[] = [];
  public templateData: TemplateData ={
      fieldNames:[],
      fieldLabels:{},
      fieldDefinitions:{},
      childType: [],
      exportPDF:{},
      exportCSV:{}
    };
  public templateSpecificData: TemplateData ={
      fieldNames:[],
      fieldLabels:{},
      fieldDefinitions:{},
      childType: [],
      exportPDF:{},
      exportCSV:{}
    };
    
  private configServiceG:ConfigServiceG;

  constructor(public _permissionService: PermissionService) {
    this.configServiceG = inject(ConfigServiceG)
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

  setDataTableObjData(
    data: {
      [key: string]: {
        data: { items: any[]; count: number; limit: number; page: number };
        objType: string;
        childType: string;
      };
    },
    configService: any,
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
    const dataTableConfig = [];
    for (const dataType in data) {
      const objType = data[dataType].objType;
      if (!allowedObjectType.includes(objType)) {
        continue;
      }
      const config = configService.config()[objType];

      const fieldNamesList = config['display_list'];
      let colNameObj: { [index: string]: any } = {};
      const labelList = config['label_list'];
      for (const key of fieldNamesList) {
        colNameObj[key] = (config['fields'][key] || [])['attribut_label'];
      }
      let currentDataTableConfig = {
        labelList: labelList,
        description_field_name: config['description_field_name'],
        childType: data[dataType].childType,
        sorts:
          'sorts' in config
            ? {
                sort_dir: config.sorts[0]['dir'] || 'asc',
                sort: config.sorts[0]['prop'],
              }
            : {},
        colNameObj: colNameObj,
        objectType: objType,
        moduleCode: moduleCode,
        canCreateObj: this._permissionService.modulePermission[objType]?.C > 0 || false,
        canCreateChild:
          this._permissionService.modulePermission[data[dataType].childType]?.C > 0 || false,
      };
      dataTableConfig.push(currentDataTableConfig);
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
    this.dataTableConfig = dataTableConfig;
  }

  fetchFieldsProperty(fields:any, property:string){
    let fieldLabels = {}
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
    const config = this.configServiceG.config()[objectType];
    console.log(config)
    this.templateData.fieldNames = config["display_properties"],
    this.templateData.childType = config['children_type'];
    this.templateData.exportPDF = config?.export_pdf
    this.templateData.exportCSV = this.configServiceG.config()["module"]?.export_csv;

    // Pas beau 
    this.templateData.fieldNames.forEach((field_name) => {
      this.templateData.fieldLabels[field_name] = config.fields[field_name]?.attribut_label;
      this.templateData.fieldDefinitions[field_name] = config.fields[field_name]?.definition;
    });
    return this.templateData;
  }

  setTemplateSpecificData(types_site:{"config":{"specific":any}}[]){
    let schemaSpecificType = {};
    let keyHtmlToPop = '';

    for (let type_site of types_site) {
      if (type_site.config && 'specific' in type_site.config) {
        const fields = type_site['config']['specific']
        // Exclusion des propriétés de type html (TODO hidden ??)
        for (const field_name in fields) {
          const field = fields[field_name];
          if (
            'type_widget' in field &&
            field['type_widget'] == 'html'
          ) {
            keyHtmlToPop = field;
          }
        }
        const { [keyHtmlToPop]: _, ...specificObjWithoutHtml } = type_site['config']['specific'];

        schemaSpecificType = Object.assign(schemaSpecificType, specificObjWithoutHtml);
      }
    }
      this.templateSpecificData = {
        fieldNames: Object.keys(schemaSpecificType),
        fieldLabels: this.fetchFieldsProperty(schemaSpecificType,"attribut_label"),
        fieldDefinitions: this.fetchFieldsProperty(schemaSpecificType,"definition"),
        childType:[],
        exportCSV :[],
        exportPDF: []
      };
    return this.templateSpecificData;
}}
