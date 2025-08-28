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
import { DatatableComponent } from '@swimlane/ngx-datatable';
import { Subject, Subscription } from 'rxjs';
import { debounceTime } from 'rxjs/operators';

import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { IColumn } from '../../interfaces/column';
import { IobjObs, ObjDataType } from '../../interfaces/objObs';
import { IPage } from '../../interfaces/page';
import { DataTableService } from '../../services/data-table.service';
import { Utils } from '../../utils/utils';
import { SelectObject } from '../../interfaces/object';
import { CommonService } from '@geonature_common/service/common.service';
import { TPermission } from '../../types/permission';
import { ObjectsPermissionMonitorings } from '../../enum/objectPermission';
import { IdataTableObjData } from '../../interfaces/geom';

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
  // Objet contenant les données des éléments à afficher dans les tableaux
  @Input() dataTableObjData: IdataTableObjData;
  // Array d'objets contenant la configuration éléments à afficher dans les tableaux
  @Input() dataTableConfig: [{ objectType: string; childType: string; label: string; config: any }];
  @Input() currentUser;
  @Input() permission: TPermission;
  @Input() bDeleteModalEmitter: EventEmitter<boolean>;
  @Input() parentPath: string;
  @Input() activetabIndex: number = 0;

  @Output() rowStatusChange = new EventEmitter<Object>();
  @Output() addVisitFromTable = new EventEmitter<Object>();
  @Output() saveOptionChildren = new EventEmitter<SelectObject>();
  @Output() bEditChange = new EventEmitter<boolean>();

  @Output() onSort = new EventEmitter<any>();
  @Output() onFilter = new EventEmitter<any>();
  @Output() onSetPage = new EventEmitter<any>();
  @Output() onDetailsRow = new EventEmitter<any>();
  @Output() tabChanged = new EventEmitter<any>();

  @Output() onDeleteEvent = new EventEmitter<any>();
  @Output() onEditEvent = new EventEmitter<any>();
  @Output() onAddChildren = new EventEmitter<any>();
  @Output() onAddObj = new EventEmitter<any>();
  @Output() objectsStatusChange: EventEmitter<Object> = new EventEmitter<Object>();

  bDeleteModal: boolean = false;
  bDeleteSpinner: boolean = false;

  private subscription: Subscription;

  private filterSubject: Subject<string> = new Subject();
  displayFilter: boolean = false;
  objectsStatus: ItemsObjectTable = {};
  //  Current object type (site, individual, visit...)
  objectType: IobjObs<ObjDataType>;
  // Columns for ngx-datatable
  columns;

  filters = {};
  // Selected rows in the table for deletion
  rowDeleted;

  canCreateObj: boolean;
  canCreateChild: boolean;

  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;

  activetabType: string;

  @ViewChild(DatatableComponent) table: DatatableComponent;
  @ViewChild('actionsTemplate') actionsTemplate: TemplateRef<any>;
  @ViewChild('hdrTpl') hdrTpl: TemplateRef<any>;

  constructor(
    private _dataTableService: DataTableService,
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
    // Initialisation des filtres
    this.clearFilters();
    this.filterSubject.pipe(debounceTime(500)).subscribe(() => {
      this.filter();
    });
  }

  changeActiveTab(tab) {
    this.activetabIndex = tab.index;
    // Réinitialisation des données selectés
    this.activetabType = this.dataTableConfig[tab.index].objectType;
    this.columns =
      this.dataTableObjData[this.activetabType].rows.length > 0
        ? this._dataTableService.colsTable(this.dataTableObjData[this.activetabType].columns)
        : null;
    this.rows = this.dataTableObjData[this.activetabType].rows;
    this.page = this.dataTableObjData[this.activetabType].page;
    this.objectsStatusChange.emit(this.reInitStatut());
    this.tabChanged.emit(this.activetabType);
    this.initPermissionAction();
  }

  initSort() {
    const configObject = this.dataTableConfig[this.activetabIndex]?.config || {};
    const sort =
      'sorts' in configObject
        ? {
            sort_dir: configObject.sorts[0]['dir'] || 'asc',
            sort: configObject.sorts[0]['prop'],
          }
        : {};
    this.filters = { ...this.filters, ...sort };
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
    // TODO inutilisé car la variable nb total sans filtre n'est pas transmise par le backend
    const nbSelected = this.dataTableObjData[chidrenType].page.count;
    const nb = this.dataTableObjData[chidrenType].page.count;
    return nb == nbSelected ? `(${nb})` : nb ? `(${nbSelected}/${nb})` : `(${nbSelected})`;
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
    this.onSetPage.emit({ page: $event, filters: this.filters, tabObj: this.activetabType });
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

  saveOptionChild($event: SelectObject) {
    this.saveOptionChildren.emit($event);
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
      case 'individual':
        objectType = ObjectsPermissionMonitorings.MONITORINGS_INDIVIDUALS;
        objectTypeChild = 'marking';
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
      if (this.dataTableConfig && this.dataTableObjData) {
        this.updateRowsAndPage();
      }
    }
  }

  private clearFilters() {
    this.filters = {};
    this.initSort();
  }

  private updateDataTable(objChanges: SimpleChange) {
    if (this.dataTableObjData && Object.keys(this.dataTableObjData).length > 0) {
      for (const objType in this.dataTableObjData) {
        this.objectsStatus[objType] = this._dataTableService.initObjectsStatus(
          this.dataTableObjData[objType].rows,
          objType
        );
      }

      this.activetabType = this.dataTableConfig[this.activetabIndex].objectType;
      const dataTable = this.dataTableObjData[this.activetabType];
      this.columns =
        dataTable.rows.length > 0 ? this._dataTableService.colsTable(dataTable.columns) : null;

      this.rows = dataTable.rows;
      this.page = dataTable.page;
      this.initPermissionAction();
    }
  }

  private updateRowsAndPage() {
    // mise à jour des données de la liste
    // et de la pagination lors d'un changement de données suite un appel API
    this.activetabType = this.dataTableConfig[this.activetabIndex].objectType;
    const dataTable = this.dataTableObjData[this.activetabType];
    this.rows = dataTable.rows || [];
    this.page = dataTable.page;
    this.initPermissionAction();
  }

  addChildrenVisit(selected) {
    this.addVisitFromTable.emit({ rowSelected: selected, objectType: this.activetabType });
  }

  navigateToAddChildren(_, row) {
    row['object_type'] = this.dataTableConfig[this.activetabIndex]['childType'];
    this.onAddChildren.emit(row);
  }

  navigateToAddObj() {
    this.onAddObj.emit(this.dataTableConfig[this.activetabIndex]['objectType']);
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
    this.rowDeleted = row;
    const varNameObjet = this.dataTableConfig[this.activetabIndex].config.description_field_name;

    this.rowDeleted['name_object'] = row[varNameObjet];
    this.bDeleteModal = true;
  }
}
