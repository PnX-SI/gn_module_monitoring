import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  SimpleChanges
} from "@angular/core";

import { FormGroup } from "@angular/forms";
import { MonitoringObject } from "../../class/monitoring-object";
import { Layer } from "@librairies/leaflet";
import { ConfigService } from "../../services/config.service";
import { DataMonitoringObjectService } from "../../services/data-monitoring-object.service";

import { MapService } from "@geonature_common/map/map.service";

@Component({
  selector: "pnx-monitoring-map",
  templateUrl: "./monitoring-map.component.html",
  styleUrls: ["./monitoring-map.component.css"]
})
export class MonitoringMapComponent implements OnInit {
  @Input() bEdit: boolean;
  @Input() obj: MonitoringObject;

  @Input() objectsStatus: Object;
  @Output() objectsStatusChange: EventEmitter<Object> = new EventEmitter<Object>();

  @Input() objForm: FormGroup;

  sites = {};

  // todo mettre en config
  styleConfig = {
    hidden: {
      opacity: 0,
      fillOpacity: 0
    },
    normal: {
      opacity: 0.7,
      fillOpacity: 0.5
    }
  };

  constructor(
    private _mapService: MapService,
    private _configService: ConfigService,
    private _data: DataMonitoringObjectService,
  ) { }


  ngOnInit() {
    this._data
      .getSites(this.obj.modulePath)
      .subscribe((sites) => {
        this.initSites(sites);
      })
  }

  initSites(sites) {
    this.sites = sites;
    setTimeout(() => {
      let $this = this;
      if (this.sites && this.sites['features']) {
        this.initSitesStatus();
        this.setSitesStyle();
        this.sites['features'].forEach(site => {

          $this.setPopup(site.id);
          let layer = $this.findSiteLayer(site.id);
          layer.on('click', (e) => {
            this.setSelectedSite(site.id)
          })
        });
      }
    }, 500);
  }

  initSitesStatus() {
    if (!this.objectsStatus['site']) {
      this.objectsStatus['site'] = [];
    }
    const $this = this;
    this.sites['features'].forEach(site => {
      const status = $this.objectsStatus['site'].find(status => status.id == site.id);
      if(status) { 
        return;
      }

      $this.objectsStatus['site'].push(
        {
          'selected': false,
          'visible': true,
          'id': site.id
        }
      );
    });
  }

  setSelectedSite(id) {
    this.objectsStatus['site'].forEach(status => {
      status['selected'] = status['id'] == id;
    });
    this.setSitesStyle();
  }

  setSitesStyle() {
    if(this.objectsStatus['site'] && this._mapService.map) {
      this.objectsStatus['site'].forEach(status => {
        this.setSiteStyle(status)
      });
    }
  }

  setSiteStyle(status) {
    let layer = this.findSiteLayer(status.id);
    if (!layer) return;

    let style = status['visible']
      ? this.styleConfig.normal
      : this.styleConfig.hidden;

    style['color'] = status['selected'] ? 'red' : 'blue';

    layer['setStyle'](style);

    if (status['selected']) {
      layer.openPopup();
    }

    if (!status['visible'] || !status['selected']) {
      layer.closePopup();
    }
  }

  findSiteLayer(id): Layer {
    let layers = this._mapService.map["_layers"];
    let layerKey = Object.keys(layers).find(key => {
      let feature = layers[key] && layers[key].feature;
      return feature && (feature['id'] == id || feature.properties['id'] == id);
    });
    return layerKey && layers[layerKey];
  }

  setPopup(id) {
    let layer = this.findSiteLayer(id);

    let ObjectLabel = this._configService.configModuleObjectParam(
      "objects",
      this.obj.modulePath,
      layer['feature'].object_type,
      "label"
    );

    let sPopup = `
    <div>
      ${ObjectLabel} ${layer['feature'].properties.description || layer['feature'].properties.base_site_name}
    </div>    
    `;

    layer.bindPopup(sPopup).closePopup();
  }

  ngOnChanges(changes: SimpleChanges) {
    for (let propName in changes) {
      let chng = changes[propName];
      let cur = chng.currentValue;
      switch (propName) {
        case "objectsStatus":
          this.setSitesStyle();
      }
    }
  }
}
