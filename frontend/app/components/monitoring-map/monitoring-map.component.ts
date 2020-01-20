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
import { Layer, svg } from "@librairies/leaflet";
import { ConfigService } from "../../services/config.service";
import { DataMonitoringObjectService } from "../../services/data-monitoring-object.service";


import { MapService } from "@geonature_common/map/map.service";
import { Utils } from '../../utils/utils'


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

  @Input() sites: {};

  panes = {};
  renderers = {};
  map;
  // todo mettre en config
  
  styles = {
    hidden: {
      opacity: 0,
      fillOpacity: 0,
      color: 'blue',
      zIndex: 0
    },
    default: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: 'blue',
      zIndex: 600
    },
    current: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: 'green',
      zIndex: 650

    },
    selected: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: 'red',
      zIndex: 660
    },
    edit: {
      opacity: 0.2,
      fillOpacity: 0.1,
      color: 'blue',
      zIndex: 600
    }
  };

  constructor(
    protected _mapService: MapService,
    private _configService: ConfigService,
    private _data: DataMonitoringObjectService,
  ) { }


  ngOnInit() {
    this.initSites();
  }

  initSites() {
    setTimeout(() => {
      let $this = this;
      this.initPanes()
      if (this.sites && this.sites['features']) {

        this.initSitesStatus();
        this.sites['features'].forEach(site => {
          $this.setPopup(site.id);
          let layer = $this.findSiteLayer(site.id);
          //pane
          layer.on('click', (e) => {
            this.setSelectedSite(site.id);
            this.objectsStatusChange.emit(Utils.copy(this.objectsStatus));
          })
        });
        this.setSitesStyle();
      }
    }, 0);
  }

  initPanes() {
    const map = this._mapService.map
    for (const key in this.styles) {
      const style = this.styles[key];
      map.createPane(key);
      const pane = map.getPane(key);
      pane.style.zIndex = style.zIndex;
      const renderer = svg({pane: pane});
      this.panes[key] = pane;
      this.renderers[key] = renderer;
    }
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
      const b_changed = status['selected'] != (status['id'] == id);
      status['selected'] = status['id'] == id;
      if (b_changed) {
        this.setSiteStyle(status);
      }
    });
  }

  setSitesStyle() {
    if(this.objectsStatus['site'] && this._mapService.map) {
      this.objectsStatus['site'].forEach(status => {
        this.setSiteStyle(status)
      });
    }
  }

  setSiteStyle(status) {
    const map = this._mapService.map;
    let layer = this.findSiteLayer(status.id);
    if (!layer) return;



    const style_name = 
      !status['visible'] ? 'hidden' :
      status['current'] ? 'current' :
      status['selected'] ? 'selected' :
      this.bEdit ? 'edit' :
      'default';

    const style = this.styles[style_name] || this.styles['default'];

    style['pane'] = this.panes[style_name];
    style['renderer'] = this.renderers[style_name];
    layer.removeFrom(map);
    layer.setStyle(style);
    layer.addTo(map);


    if (status['selected']) {

      if(!layer._popup) {
        this.setPopup(status.id);
        layer = this.findSiteLayer(status.id);
      }
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

    if(layer._popup) {
      return;
    }
    // TODO verifier si le fait de spécifier # en dur
    //  Ne pose pas de soucis pour certaine configuration
    let url = [
      '#',
      this._configService.frontendModuleMonitoringUrl(),
      'object',
      this.obj.modulePath,
      'site',
      layer['feature'].properties.id_base_site
    ].join('/');


    let sPopup = `
    <div>
      <h4>  <a href=${url}>${layer['feature'].properties.base_site_name}</a></h4>
      ${layer['feature'].properties.description || ''}
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
          break;
        case "bEdit":
          this.setSitesStyle();
          break;
      }
    }
  }
}
