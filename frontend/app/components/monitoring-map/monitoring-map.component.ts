import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';

import { FormGroup } from '@angular/forms';
import { MonitoringObject } from '../../class/monitoring-object';
import { Layer, svg, Path } from 'leaflet';
import { ConfigService } from '../../services/config.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { GeoJSONService } from '../../services/geojson.service';
import { Popup } from '../../utils/popup';
import { ActivatedRoute } from '@angular/router';

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
  @Input() objectListType: string;
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
    private _popup: Popup,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {}

  refresh_geom_data() {
    const params = {
      ...this.pre_filters,
      ...this.filters,
    };
    this._geojsonService.removeAllLayers();
    let displayObject;
    // Choix des objets a afficher
    if (this.bEdit && !this.obj.id) {
      // Si création d'un nouvel objet on n'affiche rien
      displayObject = undefined;
    } else if (this.bEdit && this.obj.id) {
      // Si modification affichage de l'objet en cours
      displayObject = this.obj.objectType;
    } else if (this.obj.objectType == 'module') {
      // Si module affichage du type d'objet courant
      displayObject = this.objectListType;
    } else if (this.obj.objectType == 'sites_group') {
      // Si page détail d'un groupe de site affichage du groupe de site et de ces enfants
      displayObject = 'sites_group_with_child';
    } else {
      // Sinon affichage des sites
      displayObject = 'site';
    }

    this._geojsonService.removeAllFeatureGroup();
    if (displayObject == 'site') {
      this._geojsonService.getSitesGroupsChildGeometries(
        this.onEachFeatureSite(this.buildQueryParams('site')),
        params
      );
    } else if (displayObject == 'sites_group') {
      this._geojsonService.getSitesGroupsGeometries(
        this.onEachFeatureGroupSite(this.buildQueryParams('sites_group')),
        params
      );
    } else if (displayObject == 'sites_group_with_child') {
      this._geojsonService.getSitesGroupsGeometriesWithSites(
        this.onEachFeatureGroupSite(this.buildQueryParams('sites_group')),
        this.onEachFeatureSite(this.buildQueryParams('site')),
        params
      );
    }
  }

  buildQueryParams(displayObject: string) {
    // Construction des queryParams
    // Important pour le paramètre parents_path qui est essentiel pour le breadcrumb
    let parents_path = ['module'];
    let current_object = this._route.snapshot.params['objectType'];

    if (!parents_path.includes(current_object) && current_object !== displayObject) {
      parents_path.push(current_object);
    }
    return { parents_path: parents_path };
  }

  onEachFeatureSite(queryParams) {
    return (feature, layer) => {
      const popup = this._popup.setSitePopup(this.obj.moduleCode, feature, queryParams);
      layer.bindPopup(popup);
    };
  }

  onEachFeatureGroupSite(queryParams) {
    return (feature, layer) => {
      const popup = this._popup.setSiteGroupPopup(this.obj.moduleCode, feature, queryParams);
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

    if (Object.keys(changes).includes('selectedObject')) {
      if (!this.selectedObject) {
        return;
      }
      if (this.obj.objectType == 'module' && Object.keys(this.selectedObject).length > 0) {
        if (this.objectListType == 'sites_group') {
          this._geojsonService.selectSitesGroupLayer(this.selectedObject['id'], true);
        } else if (this.objectListType == 'site') {
          this._geojsonService.selectSitesLayer(this.selectedObject['id'], true);
        }
      }
    }
    if (Object.keys(changes).includes('bEdit')) {
      this.setSitesStyle(this.obj.objectType);
    }

    if (
      Object.keys(changes).includes('filters') ||
      Object.keys(changes).includes('pre_filters') ||
      Object.keys(changes).includes('objectListType')
    ) {
      // Filtres du tableau
      // A appliquer que si on est au niveau du module pour les objets sites et groupes de sites
      // Ou au niveau des groupes de sites pour les sites
      if (
        Object.keys(changes).includes('filters') &&
        (this.objectListType == 'sites_group' || this.objectListType == 'site')
      ) {
        this.refresh_geom_data();
      } else if (
        Object.keys(changes).includes('pre_filters') ||
        Object.keys(changes).includes('objectListType')
      ) {
        this.refresh_geom_data();
      }
    }
  }
}
