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
const NAME_LAYER_GRP_SITE: string = 'Groupes de sites';

export type DisplayMode = 'main' | 'info' | 'info_zoom' | 'info_hidden';

/** entités déjà dessinées par la couche principale, à ne pas redessiner en "info" */
export interface ExcludedFeatures {
  property: string;
  value?: number | string;
}

interface LayerModeConfig {
  layerName: string | null;
  zoom: boolean;
  visible: boolean;
}

@Injectable()
export class GeoJSONService {
  geojsonSitesGroups: GeoJSON.FeatureCollection;
  geojsonSites: GeoJSON.FeatureCollection;
  sitesGroupFeatureGroup: L.FeatureGroup;
  sitesFeatureGroup: L.FeatureGroup;
  infoFeatureGroups: { [layerName: string]: L.FeatureGroup } = {};
  // cases cochées par l'utilisateur, captées sur les événements du layer Control ;
  // l'état de la carte ne suffit pas, il change aussi quand la page change
  private userLayerVisibility: { [layerName: string]: boolean } = {};
  private watchedMap: L.Map;
  private ownLayerChanges = 0;
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
    this.forgetInfoFeatureGroups();
  }

  private forgetInfoFeatureGroups() {
    Object.values(this.infoFeatureGroups).forEach((featureGroup) =>
      this.removeFeatureGroup(featureGroup)
    );
    this.infoFeatureGroups = {};
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
      sitesGroupstyle ?? (mode !== 'main' ? defaultSiteGroupStyleInfo : defaultSiteGroupStyle);

    const effectiveSiteStyle = sitesStyle ?? (mode !== 'main' ? defaultSiteStyleInfo : undefined);

    return forkJoin({
      sitesGroup: this._sites_group_service.get_geometries(paramsSitesGroup),
      sites: this._sites_service.get_geometries(paramsSite),
    }).subscribe((data) => {
      this.geojsonSitesGroups = data['sitesGroup'];

      this.replaceFeatureGroup(mode, 'sitesGroupFeatureGroup', cfgGroup.layerName);
      this.replaceFeatureGroup(mode, 'sitesFeatureGroup', cfgSite.layerName);

      this.storeFeatureGroup(
        this.setMapData(
          data['sitesGroup'],
          sitesGroupOnEachFeature,
          cfgGroup.layerName,
          cfgGroup.zoom,
          effectiveGroupStyle,
          cfgGroup.visible
        ),
        mode,
        'sitesGroupFeatureGroup',
        cfgGroup.layerName
      );
      this.storeFeatureGroup(
        this.setMapData(
          data['sites'],
          sitesOnEachFeature,
          cfgSite.layerName,
          false, // Toujours false car on zoom sur le groupe de site
          effectiveSiteStyle,
          cfgSite.visible
        ),
        mode,
        'sitesFeatureGroup',
        cfgSite.layerName
      );
    });
  }

  getSitesGroupsGeometries(
    onEachFeature: Function,
    params = {},
    mode: DisplayMode = 'main',
    style?,
    exclude?: ExcludedFeatures
  ) {
    const cfg = this.resolveMode(mode, NAME_LAYER_GRP_SITE);
    const effectiveStyle =
      style ?? (mode !== 'main' ? defaultSiteGroupStyleInfo : defaultSiteGroupStyle);

    this._sites_group_service
      .get_geometries(params)
      .subscribe((data: GeoJSON.FeatureCollection) => {
        this.geojsonSitesGroups = data;
        this.replaceFeatureGroup(mode, 'sitesGroupFeatureGroup', cfg.layerName);

        this.storeFeatureGroup(
          this.setMapData(
            this.excludeFeatures(data, exclude),
            onEachFeature,
            cfg.layerName,
            cfg.zoom,
            effectiveStyle,
            cfg.visible
          ),
          mode,
          'sitesGroupFeatureGroup',
          cfg.layerName
        );
      });
  }

  getSitesGroupsChildGeometries(
    onEachFeature: Function,
    params = {},
    mode: DisplayMode = 'main',
    style?,
    exclude?: ExcludedFeatures
  ) {
    const cfg = this.resolveMode(mode, NAME_LAYER_SITE);
    const effectiveStyle = style ?? (mode !== 'main' ? defaultSiteStyleInfo : undefined);

    this._sites_service.get_geometries(params).subscribe((data: GeoJSON.FeatureCollection) => {
      this.replaceFeatureGroup(mode, 'sitesFeatureGroup', cfg.layerName);

      this.storeFeatureGroup(
        this.setMapData(
          this.excludeFeatures(data, exclude),
          onEachFeature,
          cfg.layerName,
          cfg.zoom,
          effectiveStyle,
          cfg.visible
        ),
        mode,
        'sitesFeatureGroup',
        cfg.layerName
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
    style?,
    visible: boolean = true
  ): L.FeatureGroup | undefined {
    const map = this._mapService.getMap();
    if (geojson['features'] == null) {
      return undefined;
    }

    this.watchLayerControl();
    const featureGroup: L.FeatureGroup = this._mapService.createOrderedGeojson(
      geojson,
      false,
      onEachFeature,
      style
    );
    if (featureGroup.getLayers().length == 0) {
      // pas d'entrée dans le gestionnaire pour une couche sans entité
      map.removeLayer(featureGroup);
      return undefined;
    }
    this.asOurOwnChange(() => {
      if (layerName) {
        this._mapService.layerControl.addOverlay(featureGroup, layerName);
      }
      if (!visible) {
        // createOrderedGeojson l'a déjà ajoutée à la carte, la retirer pour la
        // laisser à cocher
        map.removeLayer(featureGroup);
      }
    });
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
    if (!feature || !this._mapService.map) {
      return;
    }
    this.asOurOwnChange(() => {
      if (this._mapService.map.hasLayer(feature)) {
        this._mapService.map.removeLayer(feature);
      }
      // couche "info_hidden" : déclarée mais pas affichée, son overlay est à retirer
      // même absente de la carte
      this._mapService.layerControl?.removeLayer(feature);
    });
  }

  /** cocher ou décocher est un événement du layer Control : le capter plutôt que de
      le déduire de l'état de la carte, remplacée quand la page change */
  private watchLayerControl() {
    const map = this._mapService.map;
    if (!map || this.watchedMap === map) {
      return;
    }
    this.watchedMap = map;
    map.on('overlayadd overlayremove', (e: any) => {
      if (!this.ownLayerChanges && e.name) {
        this.userLayerVisibility[e.name] = e.type === 'overlayadd';
      }
    });
  }

  /** nos ajouts et retraits émettent les mêmes événements qu'un clic, les taire */
  private asOurOwnChange(action: () => void) {
    this.ownLayerChanges++;
    try {
      action();
    } finally {
      this.ownLayerChanges--;
    }
  }

  private excludeFeatures(
    data: GeoJSON.FeatureCollection,
    exclude?: ExcludedFeatures
  ): GeoJSON.FeatureCollection {
    if (exclude?.value == null || data?.features == null) {
      return data;
    }
    // comparaison souple : id de l'URL en chaîne, propriété GeoJSON en entier
    return {
      ...data,
      features: data.features.filter((f) => f.properties[exclude.property] != exclude.value),
    };
  }

  /** retire la couche que le nouvel appel remplace : donnée principale de la carte,
      ou couche "info" de même nom */
  private replaceFeatureGroup(
    mode: DisplayMode,
    mainProperty: 'sitesFeatureGroup' | 'sitesGroupFeatureGroup',
    layerName: string | null
  ) {
    if (mode === 'main') {
      this.removeFeatureGroup(this[mainProperty]);
      return;
    }
    this.removeFeatureGroup(this.infoFeatureGroups[layerName]);
    delete this.infoFeatureGroups[layerName];
  }

  private storeFeatureGroup(
    featureGroup: L.FeatureGroup | undefined,
    mode: DisplayMode,
    mainProperty: 'sitesFeatureGroup' | 'sitesGroupFeatureGroup',
    layerName: string | null
  ) {
    if (mode === 'main') {
      this[mainProperty] = featureGroup;
    } else if (featureGroup) {
      this.infoFeatureGroups[layerName] = featureGroup;
    } else {
      delete this.infoFeatureGroups[layerName];
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
    this.forgetInfoFeatureGroups();
    this._mapService.map.eachLayer(function (layer) {
      if (layer instanceof L.FeatureGroup) {
        listFeatureGroup.push(layer);
      }
    });
    for (const featureGroup of listFeatureGroup) {
      this.removeFeatureGroup(featureGroup);
    }
  }

  removeFileLayerGroup() {
    this._mapService.removeAllLayers(this._mapService.map, this._mapService.fileLayerFeatureGroup);
  }

  /**
   * Détermine la configuration du mode d'affichage d'un layer.
   *
   * @param mode - Type d'affichage demandé ("info", "info_zoom", "info_hidden" ou "main")
   * @param layerName - Nom du layer concerné (utilisé uniquement pour les modes info)
   * @returns Un objet LayerModeConfig décrivant le comportement attendu
   */

  private resolveMode(mode: DisplayMode, layerName: string): LayerModeConfig {
    // Modes "info" :
    // - "info"      : Affichage dans le layer Control pas de zoom automatique
    // - "info_zoom" : Affichage dans le layer Control zoom forcé sur l'entité cliquée
    // - "info_hidden" : Ajout au layer Control sans affichage, à cocher par l'utilisateur
    // - "main"      : Affichage en tant qu'élement principal de la carte zoom forcé sur l'entité cliquée
    if (mode !== 'main') {
      return {
        layerName: layerName,
        zoom: mode === 'info_zoom',
        // seule la couche "à cocher" garde le choix de l'utilisateur ; en "info" et
        // "info_zoom" la couche est un repère que le formulaire attend à l'écran
        visible: mode !== 'info_hidden' || (this.userLayerVisibility[layerName] ?? false),
      };
    }
    return {
      layerName: null,
      zoom: true,
      visible: true,
    };
  }
}
