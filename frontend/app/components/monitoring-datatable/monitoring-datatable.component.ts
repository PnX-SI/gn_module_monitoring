import { DatatableComponent } from "@librairies/@swimlane/ngx-datatable";
import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  ViewChild,
  SimpleChanges
} from "@angular/core";
import { Router } from "@angular/router";
import { MonitoringObjectService } from './../../services/monitoring-object.service';

@Component({
  selector: "pnx-monitoring-datatable",
  templateUrl: "./monitoring-datatable.component.html",
  styleUrls: ["./monitoring-datatable.component.css"]
})
export class MonitoringDatatableComponent implements OnInit {
  @Input() rows;
  @Input() columns;

  @Input() child0;
  @Input() frontendModuleMonitoringUrl;

  @Input() rowStatus: Array<any>;
  @Output() rowStatusChange = new EventEmitter<Object>();

  temp;
  selected = [];
  customColumnComparator;

  @ViewChild(DatatableComponent) table: DatatableComponent;

  constructor(
    private _router: Router,
    private _monitoring: MonitoringObjectService
  ) { }

  ngOnInit() {
    this.customColumnComparator = this.customColumnComparator_()
    this.temp = [...this.rows];

    // init key_filter
    this.temp.forEach((row, index) => {
      let keyFilter = "";
      Object.keys(row).forEach(key => {
        if (key != 'id') {
          keyFilter += " " + row[key];
        }
      });
      this.temp[index]["key_filter"] = keyFilter;
    });

  }

  updateFilter(event) {
    const val = event.target.value.toLowerCase();

    // filter all

    let bChange = false;
    const temp = this.temp.filter((row, index) => {
      let bCondVisible = row.key_filter.includes(val) || !val;

      bChange = bChange || bCondVisible != this.rowStatus[index].visible;
      this.rowStatus[index]['visible'] = bCondVisible;
      this.rowStatus[index]['selected'] &= bCondVisible;


      return bCondVisible;
    });

    if (bChange) {
      this.rowStatusChange.emit(this.rowStatus);
    }
    // update the rows
    this.rows = temp;
    // Whenever the filter changes, always go back to the first page
    this.table.offset = 0;
    this.setSelected();
  }

  onRowClick(event) {
    if (!(event && event.type == 'click')) {
      return;
    }
    let id = event.row && event.row.id;

    this.rowStatus.forEach((status) => {
      let bCond = status.id == id;
      status["selected"] = bCond && !status["selected"];
    });

    this.setSelected();
    this.rowStatusChange.emit(this.rowStatus);
  }

  navigateViewObject(objectType, id) {
    this._router.navigate([
      "/",
      this.frontendModuleMonitoringUrl,
      "object",
      this.child0.modulePath,
      objectType,
      id
    ]);
  }

  setSelected() {

    if(!this.rowStatus) {
      return;
    }

    const status_selected = this.rowStatus.find(status => status.selected);
    if (!status_selected) {
      return;
    }

    const index_row_selected = this.rows.findIndex(row => row.id == status_selected.id);
    if (index_row_selected == -1) {
      return;
    }

    this.selected = [this.rows[index_row_selected]];
    this.table.offset = Math.floor((index_row_selected) / this.table._limit);
  }

  ngOnChanges(changes: SimpleChanges) {
    for (let propName in changes) {
      let chng = changes[propName];
      let cur = chng.currentValue;
      switch (propName) {
        case "rowStatus":
          this.rowStatus = cur;
          this.setSelected();
          break;
        case "child0":
          this.customColumnComparator = this.customColumnComparator_();
          break;
      }
    }
  }



  customColumnComparator_() {
    return (propA, propB, colA, colB, sortDirection) => {

      let x1 = propA, x2 = propB;

      let res = 1 - Number(sortDirection=='asc') * 2;

      if(!x1 && !x2) return 0;
      if(!x1 && x2) return -res;
      if(x1 && !x2) return res;
      
      let out = (x1 == x2) ? 0 : (x1 > x2) ? 1 : -1;

      const prop = Object.keys(colA).find(key => colA[key] == x1);
      if (!prop) {
        return out;
      }

      const schema = this.child0.schema();
      const elem = schema.find(elem => elem.attribut_name == prop);
      if (!elem) {
        return out;
      }
      const typeUtil = elem.type_widget || elem.type_util;

      switch (typeUtil) {
        case 'date':
          x1 = this._monitoring.dateFromString(x1);
          x2 = this._monitoring.dateFromString(x2);
          out = (x1 == x2) ? 0 : (x1 > x2) ? 1 : -1;
          break;
        case 'text':
          // quand les propriete sont de la forme "1.1 Nom_site"
          let v1 = this._monitoring.numberFromString(x1)
          let v2 = this._monitoring.numberFromString(x2);
          if(v1 && v2){
            if( v1[0] == v2[0]) {
              out = (v1[1] == v2[1]) ? 0 : (v1[1] > v2[1]) ? 1 : -1;
            }
            else {
              out = v1[0] > v2[0] ? 1 : -1
            }
          }
        default:
          break
      }
      return out;
    }
  }
}
