import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';

import { FormGroup } from '@angular/forms';
import { MonitoringObject } from '../../class/monitoring-object';
import { Layer, svg, Path } from 'leaflet';
import { ConfigService } from '../../services/config.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { GeoJSONService } from '../../services/geojson.service';
import { Popup } from '../../utils/popup';

import { MapService } from '@geonature_common/map/map.service';
import { MapListService } from '@geonature_common/map-list/map-list.service';
import { Utils } from '../../utils/utils';
import * as L from 'leaflet';

@Component({
  selector: 'pnx-monitoring-map',
  templateUrl: './monitoring-map.component.html',
  styleUrls: ['./monitoring-map.component.css'],
})
export class MonitoringMapComponent implements OnInit {
  @Input() bEdit: boolean;
  @Input() obj: MonitoringObject;

  @Input() selectedObject: Object;
  @Input() objForm: FormGroup;

  @Input() filters: {};
  @Input() pre_filters: {};
  @Input() objectListType: String;
  @Input() heightMap;

  bListen = true;
  panes = {};
  renderers = {};
  map;
  selectedSiteId: Number;
  currentSiteId: Number;
  publicDisplaySitesGroup: boolean = false;

  // todo mettre en config
  styles = {
    hidden: {
      opacity: 0,
      fillOpacity: 0,
      color: 'blue',
      zIndex: 0,
    },
    default: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: 'blue',
      zIndex: 600,
    },
    current: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: 'green',
      zIndex: 650,
    },
    selected: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: 'red',
      zIndex: 660,
    },
    edit: {
      opacity: 0.2,
      fillOpacity: 0.1,
      color: 'blue',
      zIndex: 600,
    },
  };

  constructor(
    protected _mapService: MapService,
    private _configService: ConfigService,
    private _data: DataMonitoringObjectService,
    private _mapListService: MapListService,
    private _geojsonService: GeoJSONService,
    private _popup: Popup
  ) {}

  ngOnInit() {}

  refresh_geom_data() {
    const params = {
      ...this.pre_filters,
      ...this.filters,
    };
    this._geojsonService.removeAllLayers();
    if (this.obj.objectType == 'module') {
      if (this.objectListType == 'sites_group') {
        this._geojsonService.getSitesGroupsGeometries(this.onEachFeatureGroupSite(), params);
      } else {
        this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), params);
      }
    } else if (this.obj.objectType == 'sites_group') {
      this._geojsonService.getSitesGroupsGeometriesWithSites(
        this.onEachFeatureGroupSite(),
        this.onEachFeatureSite(),
        params
      );
    } else {
      this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), params);
    }
  }

  onEachFeatureSite() {
    return (feature, layer) => {
      const url = [
        'object',
        this.obj.moduleCode,
        'site',
        layer['feature'].properties.id_base_site,
      ].join('/');
      const popup = this._popup.setPopup(url, feature, 'base_site_name');
      layer.bindPopup(popup);
    };
  }

  onEachFeatureGroupSite() {
    return (feature, layer) => {
      const url = [
        'object',
        this.obj.moduleCode,
        'sites_group',
        layer['feature'].properties.id_sites_group,
      ].join('/');
      const popup = this._popup.setPopup(url, feature, 'sites_group_name');
      layer.bindPopup(popup);
    };
  }
  initPanes() {
    const map = this._mapService.map;
    for (const paneKey of Object.keys(this.styles)) {
      const style = this.styles[paneKey];
      map.createPane(paneKey);
      const pane = map.getPane(paneKey);
      pane.style.zIndex = style.zIndex;
      const renderer = svg({ pane: paneKey });
      this.panes[paneKey] = pane;
      this.renderers[paneKey] = renderer;
    }
  }

  setSitesStyle(objectType = 'site') {
    if (this._configService.config()[this.obj.moduleCode]['module']['b_draw_sites_group']) {
      this.publicDisplaySitesGroup = true;
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this._mapService.map) {
      return;
    }
    for (const propName of Object.keys(changes)) {
      const chng = changes[propName];
      const cur = chng.currentValue;
      const pre = chng.currentValue;
      switch (propName) {
        case 'bEdit':
          this.setSitesStyle(this.obj.objectType);
          break;
        case 'filters':
          // Filtres du tableau
          // A appliquer que si on est au niveau du module pour les objets sites et groupes de sites
          if (
            this.obj.objectType == 'module' &&
            (this.objectListType == 'sites_group' || this.objectListType == 'site')
          ) {
            this.refresh_geom_data();
          }
          break;
        case 'pre_filters':
          this.refresh_geom_data();
          break;
        case 'objectListType':
          this.refresh_geom_data();
          break;
        case 'selectedObject':
          if (this.obj.objectType == 'module')
            if (this.objectListType == 'sites_group') {
              this._geojsonService.selectSitesGroupLayer(this.selectedObject['id'], true);
            } else if (this.objectListType == 'site') {
              this._geojsonService.selectSitesLayer(this.selectedObject['id'], true);
            }
          break;
      }
    }
  }
}
