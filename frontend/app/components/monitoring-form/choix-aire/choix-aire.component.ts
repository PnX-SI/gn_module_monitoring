import { Component, OnInit, Input, Output, EventEmitter } from "@angular/core";

@Component({
  selector: "pnx-monitoring-choix-aire",
  templateUrl: "./choix-aire.component.html",
  styleUrls: ["./choix-aire.component.css"],
})
export class MonitoringChoixAireComponent implements OnInit {
  @Input() aires: {};
  @Input() objForm;

  @Input() searchAire= '';
  @Output() searchAireChange = new EventEmitter<string>();

  aireList = [];
  constructor() {}

  ngOnInit() {}

  searchAireChanged($event) {
    this.searchAire = $event;
    this.setAireList();
    this.searchAireChange.emit(this.searchAire);
  }

  setAireList() {
    if (!this.aires) {
      return;
    }
    this.aireList = this.aires["features"].map((aire) => ({
      value: aire.id,
      text: aire.properties.base_aire_name,
    }));
    if (!this.searchAire) {
      return;
    } else {
      const arraySearch = this.searchAire.toLowerCase().split(",");
      this.aireList = this.aireList.filter((aire) => {
        let cond = false;
        for (const search of arraySearch) {
          cond = cond || aire.text.toLowerCase().includes(search);
        }
        return cond;
      });
    }
  }

  ngOnChanges(changes) {
    for (const propName of Object.keys(changes)) {
      const chng = changes[propName];
      const cur = chng.currentValue;
      const pre = chng.currentValue;
      switch (propName) {
        case "objForm": {
        }
        case "aires": {
          this.setAireList();
        }
        case "searchAire": {
          this.setAireList();
        }
      }
    }
  }
}
