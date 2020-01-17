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

@Component({
  selector: "pnx-monitoring-datatable",
  templateUrl: "./monitoring-datatable.component.html",
  styleUrls: ["./monitoring-datatable.component.css"]
})
export class MonitoringDatatableComponent implements OnInit {
  @Input() rows;
  @Input() columns;

  @Input() objectType;
  @Input() modulePath;
  @Input() frontendModuleMonitoringUrl;

  @Input() rowStatus: Array<any>;
  @Output() rowStatusChange = new EventEmitter<Object>();

  temp;
  selected = [];

  @ViewChild(DatatableComponent) table: DatatableComponent;

  constructor(private _router: Router) { }

  ngOnInit() {
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
      this.modulePath,
      objectType,
      id
    ]);
  }

  setSelected() {
    
    const status_selected = this.rowStatus.find(status => status.selected);
    if(! status_selected) {
      return;
    }

    const index_row_selected = this.rows.findIndex(row => row.id == status_selected.id);
    if(index_row_selected == -1) {
      return;
    }

    this.selected = [this.rows[index_row_selected]];
    this.table.offset =  Math.floor((index_row_selected)/this.table._limit);
  }

  ngOnChanges(changes: SimpleChanges) {
    for (let propName in changes) {
      let chng = changes[propName];
      let cur = chng.currentValue;
      switch (propName) {
        case "rowStatus":
          console.log('ngChange')
          this.rowStatus = cur;
          this.setSelected();
      }
    }
  }
}
