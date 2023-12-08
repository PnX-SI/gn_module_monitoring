import { DatatableComponent } from '@swimlane/ngx-datatable';
import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  ViewChild,
  SimpleChanges,
  TemplateRef,
} from '@angular/core';
import { Router } from '@angular/router';
import { MonitoringObjectService } from './../../services/monitoring-object.service';
import { Subject } from 'rxjs';
import { catchError, map, tap, take, debounceTime } from 'rxjs/operators';
import { CommonService } from '@geonature_common/service/common.service';
import { ObjectService } from '../../services/object.service';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';

@Component({
  selector: 'pnx-monitoring-datatable',
  templateUrl: './monitoring-datatable.component.html',
  styleUrls: ['./monitoring-datatable.component.css'],
})
export class MonitoringDatatableComponent implements OnInit {
  @Input() rows;
  @Input() columns;

  @Input() sorts;

  @Input() obj;
  @Input() child0;
  @Input() frontendModuleMonitoringUrl;

  @Input() rowStatus: Array<any>;
  @Output() rowStatusChange = new EventEmitter<Object>();

  @Output() bEditChanged = new EventEmitter<boolean>();

  @Input() currentUser;

  private filterSubject: Subject<string> = new Subject();
  private subscription: any;

  row_save;
  selected = [];
  filters = {};
  customColumnComparator;

  @ViewChild(DatatableComponent) table: DatatableComponent;
  @ViewChild('actionsTemplate') actionsTemplate: TemplateRef<any>;
  @ViewChild('hdrTpl') hdrTpl: TemplateRef<any>;

  rowSelected;
  bDeleteModal: boolean = false;
  bDeleteSpinner: boolean = false;
  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;
  canCreateChild: boolean = false;
  canDeleteObj: boolean = false;

  constructor(
    private _monitoring: MonitoringObjectService,
    private _commonService: CommonService,
    private _objectService: ObjectService
  ) {}

  ngOnInit() {
    this.initDatatable();
    this.initPermission();
  }

  initPermission() {
    // TODO: Attention ici l'ajout avec l'icon ne se fait que sur un enfant (si plusieurs enfants au même niveau , le premier sera pris pour le moment)
    const childrenType = this.child0.config.children_types[0];
    this.canCreateChild = this.currentUser?.moduleCruved[childrenType]['C'];
    this.canDeleteObj = !['site', 'sites_group'].includes(this.child0.objectType);
  }

  initDatatable() {
    this.filters = this.child0.configParam('filters');
    this.filterSubject.pipe(debounceTime(500)).subscribe(() => {
      this.filter();
    });

    this.customColumnComparator = this.customColumnComparator_();
    this.row_save = this.rows.map((e) => e);
    // on declenche les filtres (si filtre par defaut)
    setTimeout(() => {
      this.filter(true);
    }, 500);
  }

  filterInput($event) {
    this.filterSubject.next();
  }

  sort() {}

  filter(bInitFilter = false) {
    // filter all

    let bChange = false;
    const temp = this.row_save.filter((row, index) => {
      let bCondVisible = true;
      for (const key of Object.keys(this.filters)) {
        let val = this.filters[key];
        if ([null, undefined].includes(val)) {
          continue;
        }
        val = String(val).toLowerCase();
        const vals = val.split(' ');
        for (const v of vals) {
          bCondVisible = bCondVisible && (String(row[key]) || '').toLowerCase().includes(v);
        }
      }

      if (!this.rowStatus) {
        return bCondVisible;
      }
      bChange = bChange || bCondVisible !== this.rowStatus[index].visible;
      this.rowStatus[index]['visible'] = bCondVisible;
      this.rowStatus[index]['selected'] = this.rowStatus[index]['selected'] && bCondVisible;
      return bCondVisible;
    });

    if (bChange || bInitFilter) {
      this.rowStatusChange.emit(this.rowStatus);
    }
    // update the rows
    this.rows = temp;
    // Whenever the filter changes, always go back to the first page
    this.table.offset = 0;
    this.setSelected();
  }

  onRowClick(event) {
    if (!(event && event.type === 'click')) {
      return;
    }
    const id = event.row && event.row.id;

    if (!this.rowStatus) {
      return;
    }

    this.rowStatus.forEach((status) => {
      const bCond = status.id === id;
      status['selected'] = bCond && !status['selected'];
    });

    this.setSelected();
    this.rowStatusChange.emit(this.rowStatus);
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

  ngOnDestroy() {
    this.filterSubject.unsubscribe();
  }

  tooltip(column) {
    return this.child0.template.fieldDefinitions[column.prop]
      ? column.name + ' : ' + this.child0.template.fieldDefinitions[column.prop]
      : column.name;
  }

  ngOnChanges(changes: SimpleChanges) {
    for (const propName of Object.keys(changes)) {
      const chng = changes[propName];
      const cur = chng.currentValue;
      const pre = chng.currentValue;
      switch (propName) {
        case 'rowStatus':
          this.setSelected();
          break;
        case 'child0':
          this.customColumnComparator = this.customColumnComparator_();
          break;
      }
    }
  }

  customColumnComparator_() {
    return (propA, propB, colA, colB, sortDirection) => {
      let x1 = propA,
        x2 = propB;

      const res = 1 - Number(sortDirection === 'asc') * 2;

      if (!x1 && !x2) {
        return 0;
      }
      if (!x1 && x2) {
        return -res;
      }
      if (x1 && !x2) {
        return res;
      }

      let out = x1 === x2 ? 0 : x1 > x2 ? 1 : -1;

      const prop = Object.keys(colA).find((key) => colA[key] === x1);
      if (!prop) {
        return out;
      }

      const schema = this.child0.schema();
      const elem = schema[prop];
      if (!elem) {
        return out;
      }
      const typeUtil = elem.type_widget || elem.type_util;

      switch (typeUtil) {
        case 'date':
          x1 = this._monitoring.dateFromString(x1);
          x2 = this._monitoring.dateFromString(x2);
          out = x1 === x2 ? 0 : x1 > x2 ? 1 : -1;
          break;
        case 'text':
          // quand les propriete sont de la forme "1.1 Nom_site"
          const v1 = this._monitoring.numberFromString(x1);
          const v2 = this._monitoring.numberFromString(x2);
          if (v1 && v2) {
            if (v1[0] === v2[0]) {
              out = v1[1] === v2[1] ? 0 : v1[1] > v2[1] ? 1 : -1;
            } else {
              out = v1[0] > v2[0] ? 1 : -1;
            }
          }
          break;
        default:
          break;
      }
      return out;
    };
  }

  msgToaster(action) {
    // return `${action} ${this.obj.labelDu()} ${this.obj.description()} effectuée`.trim();
    return `${action}  effectuée`.trim();
  }

  onDelete(row) {
    this._commonService.regularToaster('info', this.msgToaster('Suppression'));
    this._objectService.changeDisplayingDeleteModal(this.bDeleteModal);
    this._objectService.changeSelectRow({ rowSelected: row, objectType: this.child0.objectType });
    this._objectService.currentDeleteModal.subscribe(
      (deletedModal) => (this.bDeleteModal = deletedModal)
    );
  }

  alertMessage(row) {
    this.rowSelected = row;
    this.bDeleteModal = true;
  }
}
