import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable()
export class ListService {
  /**
   * Observable that stores the current tab selected (site / site_group).
   * Null if no tab is selected.
   */
  public listType$ = new BehaviorSubject<string | null>(null);

  public get listType() {
    return this.listType$.getValue();
  }

  public set listType(value: string | null) {
    if (this.arrayTableFilters$.getValue()) {
      this.tableFilters = null;
    }
    this.listType$.next(value);
  }

  /**
   * Observable that stores the filters of then tab selected
   * Null if no tab is selected.
   */
  public tableFilters$ = new BehaviorSubject<{} | null>(null);

  public get tableFilters() {
    return this.tableFilters$.getValue();
  }

  public set tableFilters(value: {} | null) {
    this.tableFilters$.next(value);
  }

  /**
   * Observable that stores the defaults filters of all the tabs
   * Null if no tab is selected.
   */
  public arrayTableFilters$ = new BehaviorSubject<any | null>(null);

  public get arrayTableFilters() {
    return this.arrayTableFilters$.getValue();
  }

  public set arrayTableFilters(value: any | null) {
    this.arrayTableFilters$.next(value);
  }

  /**
   * Observable that stores the pre_filters based on module type and route query_params
   * Null if not selected.
   */

  public preFilters$ = new BehaviorSubject<{} | null>(null);

  public get preFilters() {
    return this.preFilters$.getValue();
  }

  public set preFilters(value: {} | null) {
    this.preFilters$.next(value);
  }

  constructor() {}
}
