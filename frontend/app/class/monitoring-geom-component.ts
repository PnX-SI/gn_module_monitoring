import { PageInfo } from "../interfaces/page";
import { JsonData } from "../types/jsondata";

const LIMIT = 10;

type callbackFunction = (pageNumber: number, filters: JsonData, tabObj:string) => void;

export class MonitoringGeomComponent {
  protected getAllItemsCallback: callbackFunction;
  protected limit = LIMIT;
  public filters = {};
  public baseFilters = {};

  constructor() {}

  setPage({page,tabObj=''}) {
    this.getAllItemsCallback(page.offset + 1, this.filters, tabObj);
  }

  setSort({filters, tabObj=''}) {
    this.filters = { ...this.baseFilters, ...filters };
    const pageNumber = 1;
    this.getAllItemsCallback(pageNumber, this.filters,  tabObj);
  }

  setFilter({filters, tabObj=''}) {
    this.filters = { ...this.baseFilters, ...filters };
    this.getAllItemsCallback(1, this.filters,tabObj);
  }
}
