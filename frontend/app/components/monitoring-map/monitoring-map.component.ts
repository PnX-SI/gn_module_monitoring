import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';

import { merge } from 'rxjs';
import { filter, distinctUntilChanged } from 'rxjs/operators';
import { isEqual } from 'lodash';

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
import { ListService } from '../../services/list.service';

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

  @Input() heightMap;

  bListen = true;
  panes = {};
  renderers = {};
  map;
  selectedSiteId: Number;
  currentSiteId: Number;
  publicDisplaySitesGroup: boolean = false;

  listObjectSubscription: any;

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
    public listService: ListService,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {
    // gestion des interractions carte list
    const tableType = ['sites_group', 'site'];

    // Souscription aux sujets :
    //   * type de l'onglet actif du datatable
    //   * filtre des datatables
    //   * préfiltres
    this.listObjectSubscription = merge(
      this.listService.listType$.pipe(filter(() => this.listService.listType$.getValue() != null)),
      this.listService.tableFilters$.pipe(
        // Si le datatable n'est ni un site, ni un groupe de sites
        //    on ne tient pas compte des filtres pour la route geométrie
        filter(() => tableType.indexOf(this.listService.listType) >= 0),
        distinctUntilChanged(isEqual)
      )
    ).subscribe(() => {
      const listType = this.listService.listType$.getValue();
      const preFilters = this.listService.preFilters;
      const tableFilters = this.listService.tableFilters$.getValue();
      // On attent l'initialisation des préfiltres et le type de datatable
      if (listType !== null && preFilters !== null) {
        // On attent l'initalisation des préfiltres pour les listes de types site et groupes de sites
        if ((tableFilters === null && tableType.indexOf(listType) < 0) || tableFilters !== null) {
          this.refresh_geom_data();
        }
      }
    });
  }

  refresh_geom_data() {
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
      displayObject = this.listService.listType;
    } else if (this.obj.objectType == 'sites_group') {
      // Si page détail d'un groupe de site affichage du groupe de site et de ces enfants
      displayObject = 'sites_group_with_child';
    } else {
      // Sinon affichage des sites
      displayObject = 'site';
    }

    this._geojsonService.removeAllFeatureGroup();
    if (displayObject == 'site') {
      const params = {
        ...this.listService.getPrefilterByType(displayObject),
        ...this.listService.tableFilters$.getValue(),
      };
      this._geojsonService.getSitesGroupsChildGeometries(
        this.onEachFeatureSite(this.buildQueryParams('site')),
        params
      );
    } else if (displayObject == 'sites_group') {
      const params = {
        ...this.listService.getPrefilterByType(displayObject),
        ...this.listService.tableFilters$.getValue(),
      };
      this._geojsonService.getSitesGroupsGeometries(
        this.onEachFeatureGroupSite(this.buildQueryParams('sites_group')),
        params
      );
    } else if (displayObject == 'sites_group_with_child') {
      const paramsSitesGroup = {
        ...this.listService.getPrefilterByType('sites_group'),
        ...this.listService.tableFilters$.getValue(),
      };
      const paramsSite = {
        ...this.listService.getPrefilterByType('site'),
        ...this.listService.tableFilters$.getValue(),
      };
      this._geojsonService.getSitesGroupsGeometriesWithSites(
        this.onEachFeatureGroupSite(this.buildQueryParams('sites_group')),
        this.onEachFeatureSite(this.buildQueryParams('site')),
        paramsSitesGroup,
        paramsSite
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
        if (this.listService.listType == 'sites_group') {
          this._geojsonService.selectSitesGroupLayer(this.selectedObject['id'], true);
        } else if (this.listService.listType == 'site') {
          this._geojsonService.selectSitesLayer(this.selectedObject['id'], true);
        }
      }
    }
    if (Object.keys(changes).includes('bEdit')) {
      this.setSitesStyle(this.obj.objectType);
    }
  }

  ngOnDestroy() {
    // Réinitalisations des paramètres
    this.listService.reinitializeObservables();
    this.listObjectSubscription.unsubscribe();
  }
}
