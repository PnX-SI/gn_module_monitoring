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

  @Output() rowStatusChange = new EventEmitter<Object>();

  @Input() filters: Object;
  @Output() onFilter = new EventEmitter<Object>();
  @Output() onDeleteRow = new EventEmitter<Object>();

  @Output() bEditChanged = new EventEmitter<boolean>();

  @Input() currentUser;

  private filterSubject: Subject<string> = new Subject();
  private subscription: any;

  row_save;
  selected = [];
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
    this.canCreateChild = !!childrenType && this.currentUser?.moduleCruved[childrenType]['C'];
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
      bChange = bChange || bCondVisible;

      return bCondVisible;
    });

    this.rowStatusChange.emit({});
    // Emmet les filtrers et le nombre de données répondant aux critères dans la liste
    this.onFilter.emit({ filters: this.filters, nb_row: temp.length });
    // update the rows
    this.rows = temp;
    // Whenever the filter changes, always go back to the first page
    this.table.offset = 0;
    this.selected = [];
  }

  setSelected(id) {
    const status_selected = id;

    if (!status_selected) {
      return;
    }
    const index_row_selected = this.table._internalRows.findIndex((row) => row.id === id);
    if (index_row_selected === -1) {
      return;
    }

    this.rows.forEach((row) => {
      const bCond = row.id === id;
      row['_internal_status_visible'] = bCond && !row['_internal_status_visible'];
    });

    this.selected = [this.table._internalRows[index_row_selected]];
    this.table.offset = Math.floor(index_row_selected / this.table._limit);
  }

  onRowClick(event) {
    if (!(event && event.type === 'click')) {
      return;
    }
    const id = event.row && event.row.id;
    this.setSelected(event.row.id);
    this.rowStatusChange.emit(event.row);
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
    this._monitoring
      .dataMonitoringObjectService()
      .deleteObject(this.obj.moduleCode, this.child0.objectType, row.id)
      .subscribe(() => {
        this._commonService.regularToaster('info', this.msgToaster('Suppression'));

        this.onDeleteRow.emit({
          rowSelected: row,
          objectType: this.child0.objectType,
        });
        this.bDeleteModal = false;
      });
  }

  alertMessage(row) {
    this.rowSelected = row;
    this.bDeleteModal = true;
  }
}
