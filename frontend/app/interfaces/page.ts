export interface IPage {
  count: number;
  limit: number;
  page: number;
}

export interface IPaginated<T> extends IPage {
  items: T[];
}
