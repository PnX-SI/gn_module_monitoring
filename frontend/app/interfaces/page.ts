export interface IPage {
  count: number;
  limit: number;
  page: number;
}

export interface IPaginated<T> extends IPage {
  items: T[];
}

// PageInfo = object given by ngx-datatable
export interface PageInfo {
  offset: number;
  pageSize: number;
  limit: number;
  count: number;
}
