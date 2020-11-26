import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  SimpleChanges
} from '@angular/core';

import { FormGroup } from '@angular/forms';
import { MonitoringObject } from '../../class/monitoring-object';
import { Layer, svg } from '@librairies/leaflet';
import { ConfigService } from '../../services/config.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';


import { MapService } from '@geonature_common/map/map.service';
import { Utils } from '../../utils/utils';
import * as L from 'leaflet';


@Component({
  selector: 'pnx-monitoring-map',
  templateUrl: './monitoring-map.component.html',
  styleUrls: ['./monitoring-map.component.css']
})
export class MonitoringMapComponent implements OnInit {
  @Input() bEdit: boolean;
  @Input() obj: MonitoringObject;

  @Input() objectsStatus: Object;
  @Output() objectsStatusChange: EventEmitter<Object> = new EventEmitter<Object>();

  @Input() objForm: FormGroup;

  @Input() sites: {};

  @Input() heightMap;

  
  bListen = true;
  panes = {};
  renderers = {};
  map;
  selectedSiteId: Number;
  currentSiteId: Number;
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
  }

  initSites() {
    console.log(this._mapService.map)
    this.removeLabels();
    setTimeout(() => {
      this.initPanes();
      if (this.sites && this.sites['features']) {
        this.initSitesStatus();
        for (const site of this.sites['features']) {
          this.setPopup(site.id);
          const layer = this.findSiteLayer(site.id);
          // pane
          const fClick = this.onLayerClick(site);
          layer.off('click', fClick);
          layer.on('click', fClick);
          //
          layer.removeFrom(this._mapService.map);
          layer.addTo(this._mapService.map);
        }

        this.setSitesStyle();
      }
    }, 0);
  }

  removeLabels() {
    if (!this._mapService.map) {
      return 
    }
    const layers =this._mapService.map['_layers'];
    for (const key of Object.keys(layers)) {
      const layer = layers[key];
      if (layer.options.removeOnInit) {
        layer.removeFrom(this._mapService.map)
      }
    }
  }

  onEachFeature = (feature, layer) => {
    const mapLabelFieldName = this.obj.configParam('map_label_field_name');
    if(!mapLabelFieldName) {
      return
    }
    const textValue = feature.resolvedProperties[mapLabelFieldName];
    if(!textValue) {
      return
    }

    var text = L.tooltip({
      permanent: true,
      direction: 'top',
      className: 'text',
      removeOnInit: true,
  })
    .setContent(textValue)
    .setLatLng(layer.getLatLng());
    text.addTo(this._mapService.map);
  }

  onLayerClick(site) {
    return (event) => {
      const id = (this.selectedSiteId === site.id) ? -1 : site.id;
      this.setSelectedSite(id);
      this.bListen=false
      this.objectsStatusChange.emit(Utils.copy(this.objectsStatus));
    };
  }

  initPanes() {
    const map = this._mapService.map;
    for (const key of Object.keys(this.styles)) {
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
      const status = $this.objectsStatus['site'].find(s => s.id === site.id);
      if (status) {
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
    if (id == this.selectedSiteId)  {
      return;
    }

    // Get old select site
    let old_s_site = this.objectsStatus["site"].filter(site => site.id == this.selectedSiteId);
    if (old_s_site.length > 0){
      old_s_site[0]['selected'] = false;
      this.setSiteStyle(old_s_site[0]);
    }

    // Get new select site
    let new_s_site = this.objectsStatus["site"].filter(site => site.id == id);
    if (new_s_site.length > 0){
      new_s_site[0]['selected'] = true;
      this.setSiteStyle(new_s_site[0]);
    }
    this.selectedSiteId = id;
  }

  setSitesStyle() {

      if (this.objectsStatus['site'] && this._mapService.map) {
        this.objectsStatus['site'].forEach(status => {
          this.setSiteStyle(status);
        });
      }
  }

  setSiteStyle(status) {
    const map = this._mapService.map;
    let layer = this.findSiteLayer(status.id);
    if (!layer) { return; }

    const style_name =
      !status['visible'] ? 'hidden' :
      status['current'] ? 'current' :
      status['selected'] ? 'selected' :
      this.bEdit ? 'edit' :
      'default';


    const style = this.styles[style_name] || this.styles['default'];

    style['pane'] = this.panes[style_name];
    style['renderer'] = this.renderers[style_name];
    // layer.removeFrom(map);
    layer.setStyle(style);
    // layer.addTo(map);


    if (status['selected']) {

      if (!layer._popup) {
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
    const layers = this._mapService.map['_layers'];
    const layerKey = Object.keys(layers).find(key => {
      const feature = layers[key] && layers[key].feature;
      return feature && (feature['id'] === id || feature.properties['id'] === id);
    });
    return layerKey && layers[layerKey];
  }

  setPopup(id) {
    const layer = this.findSiteLayer(id);

    if (layer._popup) {
      return;
    }
    // TODO verifier si le fait de spécifier # en dur
    //  Ne pose pas de soucis pour certaine configuration
    const url = [
      '#',
      this._configService.frontendModuleMonitoringUrl(),
      'object',
      this.obj.moduleCode,
      'site',
      layer['feature'].properties.id_base_site
    ].join('/');


    const sPopup = `
    <div>
      <h4>  <a href=${url}>${layer['feature'].properties.base_site_name}</a></h4>
      ${layer['feature'].properties.description || ''}
    </div>
    `;

    layer.bindPopup(sPopup).closePopup();
  }

  ngOnChanges(changes: SimpleChanges) {
    for (const propName of Object.keys(changes)) {
      const chng = changes[propName];
      const cur = chng.currentValue;
      const pre = chng.currentValue;
      switch (propName) {
        case 'objectsStatus':
          if(!this.bListen) {
            this.bListen=true;
          } else {
            this.setSitesStyle();
          }
          break;
        case 'bEdit':
          this.setSitesStyle();

          break;
        case 'sites':
          this.initSites();
      }
    }
  }
}
