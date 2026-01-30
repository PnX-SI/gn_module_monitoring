import { Injectable } from '@angular/core';
import { forkJoin } from 'rxjs';
import * as L from 'leaflet';
import { GeoJSON } from 'geojson';
import { MapService } from '@geonature_common/map/map.service';

import { SitesService, SitesGroupService } from './api-geom.service';
import { FormService } from './form.service';

// This service will be used for sites and sites groups

const defaultSiteGroupStyle = {
  fillColor: '#800080',
  fillOpacity: 0.5,
  color: '#800080',
  opacity: 0.8,
  weight: 2,
  fill: true,
  zIndex: 20,
};

const defaultSiteGroupStyleInfo = {
  fillColor: '#a48aa4ff',
  fillOpacity: 0.4,
  color: '#a48aa4ff',
  opacity: 0.7,
  weight: 2,
  fill: true,
  zIndex: 200,
};

const defaultSiteStyleInfo = {
  fillColor: '#a48aa4ff',
  fillOpacity: 0.2,
  color: '#fa3efaff',
  opacity: 0.4,
  zIndex: 300,
};

const selectedSiteGroupStyle = {
  fillColor: '#ac0000',
  fillOpacity: 0.5,
  color: '#ac0000',
  opacity: 0.8,
  weight: 2,
  fill: true,
};

const selectedSiteStyle = {
  opacity: 0.7,
  fillOpacity: 0.5,
  color: 'red',
  zIndex: 30,
};

const NAME_LAYER_SITE: string = 'Sites';
const NAME_LAYER_GRP_SITE: string = 'Groupe de sites';

export type DisplayMode = 'main' | 'info' | 'info_zoom';

interface LayerModeConfig {
  layerName: string | null;
  zoom: boolean;
  clearExisting: boolean;
}

@Injectable()
export class GeoJSONService {
  geojsonSitesGroups: GeoJSON.FeatureCollection;
  geojsonSites: GeoJSON.FeatureCollection;
  sitesGroupFeatureGroup: L.FeatureGroup;
  sitesFeatureGroup: L.FeatureGroup;
  currentLayer: any = null;

  constructor(
    private _sites_group_service: SitesGroupService,
    private _sites_service: SitesService,
    private _mapService: MapService,
    private _formService: FormService
  ) {}

  setModuleCode(moduleCode: string) {
    this._sites_group_service.setModuleCode(moduleCode);
    this._sites_service.setModuleCode(moduleCode);
  }

  removeAllLayers() {
    this.removeFeatureGroup(this.sitesGroupFeatureGroup);
    this.removeFeatureGroup(this.sitesFeatureGroup);
  }

  /*
    Affichage des groupes de sites avec leur sites associés
  */
  getSitesGroupsGeometriesWithSites(
    sitesGroupOnEachFeature: Function,
    sitesOnEachFeature: Function,
    paramsSitesGroup = {},
    paramsSite = {},
    mode: DisplayMode = 'main',
    sitesGroupstyle?,
    sitesStyle?
  ) {
    const cfgGroup = this.resolveMode(mode, NAME_LAYER_GRP_SITE);
    const cfgSite = this.resolveMode(mode, NAME_LAYER_SITE);

    const effectiveGroupStyle =
      sitesGroupstyle ??
      (mode === 'info' || mode === 'info_zoom' ? defaultSiteGroupStyleInfo : defaultSiteGroupStyle);

    const effectiveSiteStyle =
      sitesStyle ?? (mode === 'info' || mode === 'info_zoom' ? defaultSiteStyleInfo : undefined);

    return forkJoin({
      sitesGroup: this._sites_group_service.get_geometries(paramsSitesGroup),
      sites: this._sites_service.get_geometries(paramsSite),
    }).subscribe((data) => {
      this.geojsonSitesGroups = data['sitesGroup'];

      if (cfgGroup.clearExisting) this.removeFeatureGroup(this.sitesGroupFeatureGroup);
      if (cfgSite.clearExisting) this.removeFeatureGroup(this.sitesFeatureGroup);

      this.sitesGroupFeatureGroup = this.setMapData(
        data['sitesGroup'],
        sitesGroupOnEachFeature,
        cfgGroup.layerName,
        cfgGroup.zoom,
        effectiveGroupStyle
      );
      this.sitesFeatureGroup = this.setMapData(
        data['sites'],
        sitesOnEachFeature,
        cfgSite.layerName,
        false, // Toujours false car on zoom sur le groupe de site
        effectiveSiteStyle
      );
    });
  }

  getSitesGroupsGeometries(
    onEachFeature: Function,
    params = {},
    mode: DisplayMode = 'main',
    style?
  ) {
    const cfg = this.resolveMode(mode, NAME_LAYER_GRP_SITE);
    const effectiveStyle =
      style ??
      (mode === 'info' || mode === 'info_zoom' ? defaultSiteGroupStyleInfo : defaultSiteGroupStyle);

    this._sites_group_service
      .get_geometries(params)
      .subscribe((data: GeoJSON.FeatureCollection) => {
        this.geojsonSitesGroups = data;
        if (cfg.clearExisting) {
          this.removeFeatureGroup(this.sitesGroupFeatureGroup);
        }

        this.sitesGroupFeatureGroup = this.setMapData(
          data,
          onEachFeature,
          cfg.layerName,
          cfg.zoom,
          effectiveStyle
        );
      });
  }

  getSitesGroupsChildGeometries(
    onEachFeature: Function,
    params = {},
    mode: DisplayMode = 'main',
    style?
  ) {
    const cfg = this.resolveMode(mode, NAME_LAYER_SITE);
    const effectiveStyle =
      style ?? (mode === 'info' || mode === 'info_zoom' ? defaultSiteStyleInfo : undefined);

    this._sites_service.get_geometries(params).subscribe((data: GeoJSON.FeatureCollection) => {
      if (cfg.clearExisting) {
        this.removeFeatureGroup(this.sitesFeatureGroup);
      }
      this.sitesFeatureGroup = this.setMapData(
        data,
        onEachFeature,
        cfg.layerName,
        cfg.zoom,
        effectiveStyle
      );
    });
  }

  // setGeomSiteGroupFromExistingObject(geom, name:boolean = false) {
  //   this.sitesGroupFeatureGroup = this.setMapData(geom, () => {}, name ? NAME_LAYER_SITE : null, null);
  // }

  setMapData(
    geojson: GeoJSON.Geometry | GeoJSON.FeatureCollection,
    onEachFeature: Function,
    layerName: string | null,
    zoom: boolean = true,
    style?
  ): L.FeatureGroup | undefined {
    const map = this._mapService.getMap();
    if (geojson['features'] == null) {
      return undefined;
    }

    const layer: L.Layer = this._mapService.createGeojson(geojson, false, onEachFeature, style);
    const featureGroup = new L.FeatureGroup();
    featureGroup.addLayer(layer);
    this._mapService.map.addLayer(featureGroup);

    if (layerName) {
      this._mapService.layerControl.addOverlay(featureGroup, layerName);
    }
    if (zoom) {
      map.fitBounds(featureGroup.getBounds());
    }
    return featureGroup;
  }

  setMapDataWithFeatureGroup(featureGroup: L.FeatureGroup[]) {
    // ?????? usage
    for (const layer of featureGroup) {
      if (layer != undefined) {
        this._mapService.map.addLayer(layer);
      }
    }
  }

  setCurrentmapData(geom, isGeomCalculated) {
    isGeomCalculated ? (this.currentLayer = null) : (this.currentLayer = geom);
  }

  setMapBeforeEdit(geom) {
    this.currentLayer = null;
    this.setMapData(geom, () => {}, null);
  }

  removeFeatureGroup(feature: L.FeatureGroup) {
    if (feature && this._mapService.map?.hasLayer(feature)) {
      this._mapService.map.removeLayer(feature);
      this._mapService.layerControl.removeLayer(feature);
    }
  }

  onEachFeature() {}

  // Jamais appelé
  // filterSitesGroups(siteGroupId: number) {
  //   if (this.geojsonSitesGroups !== undefined) {
  //     const features = this.geojsonSitesGroups.features.filter(
  //       (feature) => feature.properties.id_sites_group == siteGroupId
  //     );
  //     this.geojsonSitesGroups.features = features;
  //     this.removeFeatureGroup(this.sitesGroupFeatureGroup);
  //     this.setMapData(this.geojsonSitesGroups, this.onEachFeature, null, defaultSiteGroupStyle);
  //   }
  // }

  selectSitesGroupLayer(id: number, zoom: boolean) {
    this.sitesGroupFeatureGroup.eachLayer((layer) => {
      if (layer instanceof L.GeoJSON) {
        layer.eachLayer((sublayer: L.GeoJSON) => {
          const feature = sublayer.feature as GeoJSON.Feature;
          if (feature.properties['id_sites_group'] == id) {
            if (zoom == true) {
              const featureGroup = new L.FeatureGroup();
              featureGroup.addLayer(sublayer);
              this._mapService.map.fitBounds(featureGroup.getBounds());
            }
            sublayer.openPopup();
            return;
          }
        });
      }
    });
  }

  removeLayerByIdSite(id: number) {
    const layers = this.selectSitesLayer(id, false);
    this.removeFeatureGroup(layers);
  }

  selectSitesLayer(id: number, zoom: boolean) {
    const layers = this.sitesFeatureGroup.eachLayer((layer) => {
      if (layer instanceof L.GeoJSON) {
        layer.eachLayer((sublayer: L.GeoJSON) => {
          const feature = sublayer.feature as GeoJSON.Feature;
          if (feature.properties['id_base_site'] == id) {
            if (zoom == true) {
              const featureGroup = new L.FeatureGroup();
              featureGroup.addLayer(sublayer);
              this._mapService.map.fitBounds(featureGroup.getBounds());
            }
            sublayer.openPopup();
            return;
          }
        });
      }
    });
    return layers;
  }

  removeAllFeatureGroup() {
    let listFeatureGroup: L.FeatureGroup[] = [];
    if (!this._mapService.map) {
      return;
    }
    this._mapService.map.eachLayer(function (layer) {
      if (layer instanceof L.FeatureGroup) {
        listFeatureGroup.push(layer);
      }
    });
    for (const featureGroup of listFeatureGroup) {
      this.removeFeatureGroup(featureGroup);
      this._mapService.layerControl.removeLayer(featureGroup);
    }
  }

  removeFileLayerGroup() {
    this._mapService.removeAllLayers(this._mapService.map, this._mapService.fileLayerFeatureGroup);
  }

  /**
   * Détermine la configuration du mode d'affichage d'un layer.
   *
   * @param mode - Type d'affichage demandé ("info", "info_zoom" ou "main")
   * @param layerName - Nom du layer concerné (utilisé uniquement pour les modes info)
   * @returns Un objet LayerModeConfig décrivant le comportement attendu
   */

  private resolveMode(mode: DisplayMode, layerName: string): LayerModeConfig {
    // Modes "info" :
    // - "info"      : Affichage dans le layer Control pas de zoom automatique
    // - "info_zoom" : Affichage dans le layer Control zoom forcé sur l'entité cliquée
    // - "main"      : Affichage en tant qu'élement principal de la carte zoom forcé sur l'entité cliquée
    if (mode === 'info' || mode === 'info_zoom') {
      return {
        layerName: layerName,
        zoom: mode === 'info_zoom',
        clearExisting: this.testLayerControlExists(layerName), // test si le layer est déjà présent dans Layercontrol
      };
    }
    return {
      layerName: null,
      zoom: true,
      clearExisting: true, // en "main", on nettoye les données à chaque appel
    };
  }

  /**
   * Vérifie si un layer  (défini par son nom)  existe déjà
   * dans le LayerControl de la carte.
   *
   * @param layerName - Nom du layer à rechercher
   * @returns true si un overlay du LayerControl possède ce nom, sinon false
   */
  private testLayerControlExists(layerName: string): boolean {
    const layers = this._mapService.layerControl?.['_layers'] ?? [];
    const overlayNames = new Set(layers.filter((o: any) => o?.overlay).map((o: any) => o?.name));
    if (overlayNames.has(layerName)) {
      return true;
    }
    return false;
  }
}
