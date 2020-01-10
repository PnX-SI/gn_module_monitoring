import { DatatableComponent } from "@librairies/@swimlane/ngx-datatable";
import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  ViewChild
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

  @ViewChild(DatatableComponent) table: DatatableComponent;

  constructor(private _router: Router) {}

  ngOnInit() {
    this.temp = [...this.rows];

    // init key_filter
    this.temp.forEach((row, index) => {
      let keyFilter = "";
      Object.keys(row).forEach(key => {
        if (key != 'id') {
          keyFilter += " "+ row[key];
        }
      });
      this.temp[index]["key_filter"] = keyFilter;
    });

    if (!Object.keys(this.rowStatus).length) {
      this.rows.forEach(row => {
        this.rowStatus.push({ id: row.id, visible: true, selected: false });
      });
    }
  }

  updateFilter(event) {
    const val = event.target.value.toLowerCase();

    // filter all

    let bChange = false;
    const temp = this.temp.filter((row, index) => {
      let bCondVisible = row.key_filter.includes(val) || !val;

      bChange = bChange || bCondVisible != this.rowStatus[index].visible;
      this.rowStatus[index]['visible'] = bCondVisible;

      return bCondVisible;
    });

    if (bChange) {
      this.rowStatusChange.emit(this.rowStatus);
    }
    // update the rows
    this.rows = temp;
    // Whenever the filter changes, always go back to the first page
    this.table.offset = 0;
  }

  onRowClick(event) {
    if (!(event && event.type == 'click')) {
      return;
    }
    let id = event.row && event.row.id;
    this.rowStatus.forEach((status, index) => {
      let bCond = status.id == id;
      status["selected"] = bCond && !status["selected"];
    });

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

}
