import { PageInfo } from "../interfaces/page";
import { JsonData } from "../types/jsondata";

const LIMIT = 10;

type callbackFunction = (pageNumber: number, filters: JsonData) => void;

export class MonitoringGeomComponent {
  protected getAllItemsCallback: callbackFunction;
  protected limit = LIMIT;
  public filters = {};
  public baseFilters = {};

  constructor() {}

  setPage(page: PageInfo) {
    this.getAllItemsCallback(page.offset + 1, this.filters);
  }

  setSort(filters: JsonData) {
    this.filters = { ...this.baseFilters, ...filters };
    const pageNumber = 1;
    this.getAllItemsCallback(pageNumber, this.filters);
  }

  setFilter(filters) {
    this.filters = { ...this.baseFilters, ...filters };
    this.getAllItemsCallback(1, this.filters);
  }
}
