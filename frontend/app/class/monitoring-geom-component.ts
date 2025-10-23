import { IdataTableObjData } from '../interfaces/geom';
import { PermissionService } from '../services/permission.service';
import { JsonData } from '../types/jsondata';

const LIMIT = 10;

type callbackFunction = (pageNumber: number, filters: JsonData, tabObj: string) => void;

export class MonitoringGeomComponent {
  protected getAllItemsCallback: callbackFunction;
  protected limit = LIMIT;
  public filters = {};
  public baseFilters = {};

  public dataTableObjData: IdataTableObjData;
  public dataTableConfig: {}[] = [];
  public templateData: {} = {};

  constructor(public _permissionService: PermissionService) {}

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
          this._permissionService.modulePermission[data[dataType].childType]?.C > 0 ||
          false,
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

  setTemplateData(configService: any, objectType: string) {
    /**
     * Initialisation des données de configuration pour monitoring-properties-template
     *
     * @param {any}
     * configService service de configuration
     * objectType type d'objet
     * @returns {void}
     */
    const config = configService.config()[objectType];
    this.templateData = {
      labelList: config['label_list'],
      description_field_name: config['description_field_name'],
      childType: config['childType'],
    };
  }
}
