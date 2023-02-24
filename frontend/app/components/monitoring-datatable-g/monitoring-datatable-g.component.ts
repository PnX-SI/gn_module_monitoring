import { DatatableComponent } from "@swimlane/ngx-datatable";
import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  ViewChild,
  SimpleChanges,
  TemplateRef,
} from "@angular/core";
import { Router, ActivatedRoute } from "@angular/router";
import { Subject } from "rxjs";
import { debounceTime } from "rxjs/operators";
import { DataTableService } from "../../services/data-table.service";
import { IColumn } from "../../interfaces/column";
import { IPage } from "../../interfaces/page";
import { ObjectService } from "../../services/object.service";

interface ItemObjectTable {
  id: number | null;
  selected: boolean;
  visible: boolean;
  current: boolean;
}
type ItemsObjectTable = { [key: string]: ItemObjectTable };

@Component({
  selector: "pnx-monitoring-datatable-g",
  templateUrl: "./monitoring-datatable-g.component.html",
  styleUrls: ["./monitoring-datatable-g.component.css"],
})
export class MonitoringDatatableGComponent implements OnInit {
  @Input() rows;
  @Input() colsname: IColumn[];
  @Input() page: IPage = { count: 0, limit: 0, page: 0 };
  @Input() obj;

  @Input() rowStatus: Array<any>;
  @Output() rowStatusChange = new EventEmitter<Object>();

  @Output() bEditChanged = new EventEmitter<boolean>();

  @Input() currentUser;

  @Output() onSort = new EventEmitter<any>();
  @Output() onFilter = new EventEmitter<any>();
  @Output() onSetPage = new EventEmitter<any>();
  @Output() onDetailsRow = new EventEmitter<any>();
  @Output() addEvent = new EventEmitter<any>();

  private filterSubject: Subject<string> = new Subject();
  displayFilter: boolean = false;
  objectsStatus: ItemsObjectTable;

  objectType: string = "";
  columns;
  row_save;
  selected = [];
  filters = {};

  @ViewChild(DatatableComponent) table: DatatableComponent;
  @ViewChild("actionsTemplate") actionsTemplate: TemplateRef<any>;
  @ViewChild("hdrTpl") hdrTpl: TemplateRef<any>;

  constructor(
    private _dataTableService: DataTableService,
    private _objService: ObjectService,
    private router: Router,
    private _Activatedroute: ActivatedRoute
  ) {}

  ngOnInit() {
    this.initDatatable();
  }

  initDatatable() {
    // IF prefered  observable compare to ngOnChanges   uncomment this:
    // this._dataTableService.currentCols.subscribe(newCols => { this.columns = newCols })
    this._objService.currentObjectType.subscribe((newObjType) => {
      this.objectType = newObjType;
    });

    this.filters = {};
    this.filterSubject.pipe(debounceTime(500)).subscribe(() => {
      this.filter();
    });
  }

  onSortEvent($event) {
    this.filters = {
      ...this.filters,
      sort: $event.column.prop,
      sort_dir: $event.newValue,
    };
    this.onSort.emit(this.filters);
  }

  setPage($event) {
    this.onSetPage.emit($event);
  }

  filterInput($event) {
    this.filterSubject.next();
  }

  filter(bInitFilter = false) {
    // filter all
    const oldFilters = this.filters;
    this.filters = Object.keys(oldFilters).reduce(function (r, e) {
      if (![undefined, "", null].includes(oldFilters[e])) r[e] = oldFilters[e];
      return r;
    }, {});
    this.onFilter.emit(this.filters);
  }

  onSelectEvent({ selected }) {
    const id = selected[0].id_group_site;

    if (!this.rowStatus) {
      return;
    }

    this.rowStatus.forEach((status) => {
      const bCond = status.id === id;
      status["selected"] = bCond && !status["selected"];
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

  // tooltip(column) {
  //   return this.child0.template.fieldDefinitions[column.prop]
  //     ? column.name + " : " + this.child0.template.fieldDefinitions[column.prop]
  //     : column.name;
  // }

  ngOnChanges(changes: SimpleChanges) {
    // IF prefered ngOnChanges compare to observable   uncomment this:
    if (changes["rows"] && this.rows && this.rows.length > 0) {
      this.columns = this._dataTableService.colsTable(
        this.colsname,
        this.rows[0]
      );
    }

    if (changes["colsname"]) {
      this.filters = {};
    }

    if (changes["obj"] && this.obj) {
      this.objectsStatus,
        (this.rowStatus = this._dataTableService.initObjectsStatus(
          this.obj,
          "sites_groups"
        ));
    }
    for (const propName of Object.keys(changes)) {
      switch (propName) {
        case "rowStatus":
          this.setSelected();
          break;
      }
    }
  }
  navigateToAddChildren(_, rowId) {
    this.addEvent.emit(rowId);
    this.router.navigate(["create"], {
      relativeTo: this._Activatedroute,
    });
  }
  navigateToDetail(row) {
    row["id"] = row.pk;
    this.onDetailsRow.emit(row);
  }
}
