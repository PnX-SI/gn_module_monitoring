import { IdataTableObjData } from '../interfaces/geom';
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

  constructor() {}

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
        objConfig: { objectType: string; dataTable: { colNameObj: any } };
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
    const dataTableObjData = {} as IdataTableObjData;
    const dataTableConfig = [];

    for (const dataType in data) {
      if (!data[dataType].objConfig) {
        continue;
      }
      const objType: string = data[dataType].objConfig.objectType;
      if (!allowedObjectType.includes(objType)) {
        continue;
      }

      const config = configService.configModuleObject(moduleCode, objType);
      data[dataType].objConfig['config'] = config;
      dataTableConfig.push(data[dataType].objConfig);
      dataTableObjData[objType] = {
        columns: data[dataType].objConfig.dataTable.colNameObj,
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
}
