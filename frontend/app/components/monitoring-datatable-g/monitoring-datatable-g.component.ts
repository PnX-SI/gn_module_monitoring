import {
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  SimpleChanges,
  SimpleChange,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DatatableComponent } from '@swimlane/ngx-datatable';
import { Subject, Subscription } from 'rxjs';
import { debounceTime } from 'rxjs/operators';

import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { IColumn } from '../../interfaces/column';
import { IobjObs, ObjDataType } from '../../interfaces/objObs';
import { IPage } from '../../interfaces/page';
import { DataTableService } from '../../services/data-table.service';
import { ObjectService } from '../../services/object.service';
import { Utils } from '../../utils/utils';
import { SelectObject } from '../../interfaces/object';
import { CommonService } from '@geonature_common/service/common.service';
import { TPermission } from '../../types/permission';
import { ObjectsPermissionMonitorings } from '../../enum/objectPermission';

interface ItemObjectTable {
  id: number | null;
  selected: boolean;
  visible: boolean;
  current: boolean;
}
type ItemsObjectTable = { [key: string]: ItemObjectTable[] };

@Component({
  selector: 'pnx-monitoring-datatable-g',
  templateUrl: './monitoring-datatable-g.component.html',
  styleUrls: ['./monitoring-datatable-g.component.css'],
})
export class MonitoringDatatableGComponent implements OnInit {
  @Input() rows;
  @Input() colsname: IColumn[];
  @Input() page: IPage = { count: 0, limit: 0, page: 0 };
  @Input() obj;
  @Input() dataTableObj;
  @Input() dataTableArray;

  @Input() rowStatus: Array<any>;
  @Output() rowStatusChange = new EventEmitter<Object>();
  @Output() addFromTable = new EventEmitter<Object>();
  @Output() saveOptionChildren = new EventEmitter<SelectObject>();
  @Output() bEditChanged = new EventEmitter<boolean>();
  @Input() currentUser;
  @Input() permission: TPermission;

  @Output() onSort = new EventEmitter<any>();
  @Output() onFilter = new EventEmitter<any>();
  @Output() onSetPage = new EventEmitter<any>();
  @Output() onDetailsRow = new EventEmitter<any>();
  @Output() addEvent = new EventEmitter<any>();
  @Output() tabChanged = new EventEmitter<any>();

  @Output() onDeleteEvent = new EventEmitter<any>();
  @Output() onEditEvent = new EventEmitter<any>();

  @Input() bDeleteModalEmitter: EventEmitter<boolean>;
  bDeleteModal: boolean = false;
  bDeleteSpinner: boolean = false;

  private subscription: Subscription;

  private filterSubject: Subject<string> = new Subject();
  displayFilter: boolean = false;
  objectsStatus: ItemsObjectTable = {};

  objectType: IobjObs<ObjDataType>;
  columns;
  row_save;
  selected = [];
  filters = {};

  rowSelected;

  canCreateObj: boolean;
  canCreateChild: boolean;

  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;

  @Input() activetabIndex: number = 0;
  activetabType: string;

  @Output() objectsStatusChange: EventEmitter<Object> = new EventEmitter<Object>();

  @ViewChild(DatatableComponent) table: DatatableComponent;
  @ViewChild('actionsTemplate') actionsTemplate: TemplateRef<any>;
  @ViewChild('hdrTpl') hdrTpl: TemplateRef<any>;

  constructor(
    private _dataTableService: DataTableService,
    private _objService: ObjectService,
    private router: Router,
    private _Activatedroute: ActivatedRoute,
    private _commonService: CommonService
  ) {}

  ngOnInit() {
    this.subscribeToParentEmitter();
    this.initDatatable();
  }
  subscribeToParentEmitter(): void {
    if (this.bDeleteModalEmitter) {
      this.subscription = this.bDeleteModalEmitter.subscribe((data: boolean) => {
        this.bDeleteModal = this.bDeleteSpinner = false;
      });
    }
  }

  initDatatable() {
    // IF prefered  observable compare to ngOnChanges   uncomment this:
    // this._dataTableService.currentCols.subscribe(newCols => { this.columns = newCols })
    // this._objService.currentObjectType.subscribe((newObjType) => {
    //   this.objectType = newObjType;
    // });

    this.filters = {};
    this.filterSubject.pipe(debounceTime(500)).subscribe(() => {
      this.filter();
    });
  }

  changeActiveTab(tab) {
    this.activetabIndex = tab.index;
    // Réinitialisation des données selectés
    this.activetabType = this.dataTableArray[tab.index].objectType;
    this.dataTableObj[this.activetabType].rows.length > 0
      ? (this.columns = this._dataTableService.colsTable(
          this.dataTableObj[this.activetabType].columns,
          this.dataTableObj[this.activetabType].rows[0]
        ))
      : null;
    this.rows = this.dataTableObj[this.activetabType].rows;
    this.page = this.dataTableObj[this.activetabType].page;
    this.objectsStatusChange.emit(this.reInitStatut());
    this.tabChanged.emit(this.activetabType);
    this.initPermissionAction();
  }

  reInitStatut() {
    let status_type = Utils.copy(this.objectsStatus);
    for (let typeObject in status_type) {
      if (Array.isArray(status_type[typeObject])) {
        for (let i in status_type[typeObject]) {
          try {
            status_type[typeObject][i]['selected'] = false;
          } catch (error) {
            console.error(error.message, status_type[typeObject][i]);
          }
        }
      }
    }
    return status_type;
  }

  displayNumber(chidrenType) {
    if (!this.objectsStatus[chidrenType]) {
      return '';
    }
    const visibles = this.objectsStatus[chidrenType].filter((s) => s.visible);
    // const nbSelected = visibles.length;
    const nbSelected = this.dataTableObj[chidrenType].page.count;
    const nb = this.dataTableObj[chidrenType].page.total;
    return nb == nbSelected ? `(${nb})` : `(${nbSelected}/${nb})`;
  }

  onSortEvent($event) {
    this.filters = {
      ...this.filters,
      sort: $event.column.prop,
      sort_dir: $event.newValue,
    };
    this.onSort.emit({ filters: this.filters, tabObj: this.activetabType });
  }

  setPage($event) {
    this.onSetPage.emit({ page: $event, tabObj: this.activetabType });
  }

  filterInput($event) {
    this.filterSubject.next();
  }

  filter(bInitFilter = false) {
    // filter all
    const oldFilters = this.filters;
    this.filters = Object.keys(oldFilters).reduce(function (r, e) {
      if (![undefined, '', null].includes(oldFilters[e])) r[e] = oldFilters[e];
      return r;
    }, {});
    this.onFilter.emit({ filters: this.filters, tabObj: this.activetabType });
  }

  onRowClick(event) {
    if (!(event && event.type === 'click')) {
      return;
    }
    switch (this.activetabType) {
      case 'sites_group':
        this.rowStatusChange.emit([this.activetabType, event.row.id_sites_group]);
        break;
      case 'site':
        this.rowStatusChange.emit([this.activetabType, event.row.id_base_site]);
        break;
    }
  }

  addChildren(selected) {
    this.addFromTable.emit({ rowSelected: selected, objectType: this.activetabType });
  }

  saveOptionChild($event: SelectObject) {
    this.saveOptionChildren.emit($event);
  }

  setSelected() {
    // this.table._internalRows permet d'avoir les ligne triées et d'avoir les bons index
    if (!this.rowStatus) {
      return;
    }

    const status_selected = this.rowStatus.find((status) => status.selected);
    if (!status_selected) {
      return;
    }

    const index_row_selected = this.table._internalRows.findIndex(
      (row) => row.id === status_selected.id
    );
    if (index_row_selected === -1) {
      return;
    }

    this.selected = [this.table._internalRows[index_row_selected]];
    this.table.offset = Math.floor(index_row_selected / this.table._limit);
  }

  initPermissionAction() {
    let objectType: ObjectsPermissionMonitorings | string;
    let objectTypeChild: ObjectsPermissionMonitorings | string;
    switch (this.activetabType) {
      case 'sites_group':
        objectType = ObjectsPermissionMonitorings.MONITORINGS_GRP_SITES;
        objectTypeChild = ObjectsPermissionMonitorings.MONITORINGS_SITES;
        this.canCreateChild = this.permission[objectTypeChild].canCreate ? true : false;
        break;
      case 'site':
        objectType = ObjectsPermissionMonitorings.MONITORINGS_SITES;
        objectTypeChild = 'visit';
        this.canCreateChild = true;
        break;
      case 'visit':
        objectType = 'visit';
        objectTypeChild = 'undefined';
        this.canCreateObj = true;
        this.canCreateChild = true;
        break;
      default:
        objectType = 'undefined';
        objectTypeChild = 'undefined';
        this.canCreateObj = false;
        this.canCreateChild = false;
    }

    if (!['undefined', 'visit'].includes(objectType)) {
      this.canCreateObj = this.permission[objectType].canCreate ? true : false;
    }
  }

  ngOnDestroy() {
    this.filterSubject.unsubscribe();
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  // tooltip(column) {
  //   return this.child0.template.fieldDefinitions[column.prop]
  //     ? column.name + " : " + this.child0.template.fieldDefinitions[column.prop]
  //     : column.name;
  // }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.activetabIndex) {
      this.clearFilters();
    }

    if (changes.obj) {
      this.updateDataTable(changes.obj);
    }

    if (changes.rows || changes.page) {
      this.updateRowsAndPage();
    }

    for (const propName of Object.keys(changes)) {
      switch (propName) {
        case 'rowStatus':
          this.setSelected();
          break;
      }
    }
  }

  private clearFilters() {
    this.filters = {};
  }

  private updateDataTable(objChanges: SimpleChange) {
    if (this.dataTableObj && Object.keys(this.dataTableObj).length > 0) {
      for (const objType in this.dataTableObj) {
        this.objectsStatus[objType] = this._dataTableService.initObjectsStatus(
          this.dataTableObj[objType].rows,
          objType
        );
      }

      this.activetabType = this.dataTableArray[this.activetabIndex].objectType;
      const dataTable = this.dataTableObj[this.activetabType];
      if (dataTable.rows.length > 0) {
        this.columns = this._dataTableService.colsTable(dataTable.columns, dataTable.rows[0]);
      }
      this.rows = dataTable.rows;
      this.page = dataTable.page;
      this.initPermissionAction();
    }
  }

  private updateRowsAndPage() {
    if (this.rows && this.rows.length > 0) {
      this.activetabType = this.dataTableArray[this.activetabIndex].objectType;
      const dataTable = this.dataTableObj[this.activetabType];
      this.rows = dataTable.rows;
      this.page = dataTable.page;
      this.initPermissionAction();
    }
  }
  navigateToAddChildren(_, row) {
    this.addEvent.emit(row);
    this._objService.changeObjectType(this.dataTableArray[this.activetabIndex]);
    if (row && this.dataTableArray.length == 1) {
      row['id'] = row[row.pk];
      this.router.navigate([row.id, 'create'], {
        relativeTo: this._Activatedroute,
      });
    }
  }

  navigateToAddObj() {
    this._objService.changeObjectType(this.dataTableArray[this.activetabIndex]);
    if (this.dataTableArray.length == 1) {
      this.router.navigate(['create'], {
        relativeTo: this._Activatedroute,
      });
    } else {
      this.router.navigate([
        'monitorings',
        this.dataTableArray[this.activetabIndex].routeBase,
        'create',
      ]);
    }

    // TODO: gérer la gestion de l'ajout (et ajout d'objet enfant) d'objet de type "site" depuis la page d'accueil de visualisation de groupe de site/ site
    //
  }

  navigateToDetail(row) {
    row['id'] = row.pk;
    this.onDetailsRow.emit(row);
  }

  editSelectedItem(row) {
    row['id'] = row.pk;
    this.onEditEvent.emit(row);
  }

  msgToaster(action) {
    // return `${action} ${this.obj.labelDu()} ${this.obj.description()} effectuée`.trim();
    return `${action}  effectuée`.trim();
  }

  onDelete(row) {
    this.bDeleteSpinner = true;
    row['id'] = row[row.pk];
    this._commonService.regularToaster('info', this.msgToaster('Suppression'));
    this.onDeleteEvent.emit({ rowSelected: row, objectType: this.activetabType });
  }

  alertMessage(row) {
    row['id'] = row[row.pk];
    this.rowSelected = row;
    const varNameObjet = this.dataTableArray[this.activetabIndex].config.description_field_name;

    this.rowSelected['name_object'] = row[varNameObjet];
    this.bDeleteModal = true;
  }

  // TODO: Comprendre le fonctionnement de ObjectStatuts et RowsStatus
  // initObjectsStatus() {
  //   const objectsStatus = {};
  //   for (const childrenType of Object.keys(this.obj.children)) {
  //     objectsStatus[childrenType] = this.obj.children[childrenType].map(
  //       (child) => {
  //         return {
  //           id: child.id,
  //           selected: false,
  //           visible: true,
  //           current: false,
  //         };
  //       }
  //     );
  //   }

  //   // init site status
  //   if (this.obj.siteId) {
  //     objectsStatus["site"] = [];
  //     this.sites["features"].forEach((f) => {
  //       // determination du site courrant
  //       let cur = false;
  //       if (f.properties.id_base_site == this.obj.siteId) {
  //         cur = true;
  //       }

  //       objectsStatus["site"].push({
  //         id: f.properties.id_base_site,
  //         selected: false,
  //         visible: true,
  //         current: cur,
  //       });
  //     });
  //   }

  //   this.objectsStatus = objectsStatus;
  // }
}
