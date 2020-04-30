import { Component, OnInit, Input, Output, EventEmitter } from "@angular/core";

@Component({
  selector: "pnx-monitoring-choix-site",
  templateUrl: "./choix-site.component.html",
  styleUrls: ["./choix-site.component.css"],
})
export class MonitoringChoixSiteComponent implements OnInit {
  @Input() sites: {};
  @Input() objForm;

  @Input() searchSite= '';
  @Output() searchSiteChange = new EventEmitter<boolean>();

  siteList = [];

  constructor() {}

  ngOnInit() {}

  searchSiteChanged($event) {
    this.searchSite = $event;
    this.setSiteList();
    this.searchSiteChange.emit(this.searchSite);
  }

  setSiteList() {
    if (!this.sites) {
      return;
    }
    this.siteList = this.sites["features"].map((site) => ({
      value: site.id,
      text: site.properties.base_site_name,
    }));
    if (!this.searchSite) {
      return;
    } else {
      const arraySearch = this.searchSite.toLowerCase().split(",");
      this.siteList = this.siteList.filter((site) => {
        let cond = false;
        for (const search of arraySearch) {
          cond = cond || site.text.toLowerCase().includes(search);
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
        case "sites": {
          this.setSiteList();
        }
        case "searchSite": {
          this.setSiteList();
        }
      }
    }
  }
}
