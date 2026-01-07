import { Injectable } from '@angular/core';
import { forkJoin } from 'rxjs';
import * as L from 'leaflet';
import { GeoJSON } from 'geojson';
import { MapService } from '@geonature_common/map/map.service';

import { SitesService, SitesGroupService } from './api-geom.service';
import { ConfigService } from './config.service';

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

@Injectable()
export class GeoJSONService {
  geojsonSitesGroups: GeoJSON.FeatureCollection;
  geojsonSites: GeoJSON.FeatureCollection;
  sitesGroupFeatureGroup: L.FeatureGroup;
  currentLayer: any = null;
  sitesLayerGroup: L.FeatureGroup | L.MarkerClusterGroup;

  constructor(
    private _sites_group_service: SitesGroupService,
    private _sites_service: SitesService,
    private _mapService: MapService,
    public _configService: ConfigService
  ) {
    this.sitesLayerGroup = this._createSitesLayerGroup();
  }

  setModuleCode(moduleCode: string) {
    this._sites_group_service.setModuleCode(moduleCode);
    this._sites_service.setModuleCode(moduleCode);
  }

  removeAllLayers() {
    this.removeLayerGroup(this.sitesGroupFeatureGroup);
    this.removeSitesLayerGroup();
  }

  /*
    Affichage des groupes de sites avec leur sites associés
  */
  getSitesGroupsGeometriesWithSites(
    sitesGroupOnEachFeature: Function,
    sitesOnEachFeature: Function,
    paramsSitesGroup = {},
    paramsSite = {},
    sitesGroupstyle?,
    sitesStyle?
  ) {
    return forkJoin({
      sitesGroup: this._sites_group_service.get_geometries(paramsSitesGroup),
      sites: this._sites_service.get_geometries(paramsSite),
    }).subscribe((data) => {
      this.geojsonSitesGroups = data['sitesGroup'];
      this.removeSitesGroupLayerGroup();
      this.sitesGroupFeatureGroup = this.setMapData(
        data['sitesGroup'],
        sitesGroupOnEachFeature,
        sitesGroupstyle || defaultSiteGroupStyle,
        false
      );
      this.removeSitesLayerGroup();
      this.sitesLayerGroup = this.setMapData(data['sites'], sitesOnEachFeature, sitesStyle);
    });
  }

  getSitesGroupsGeometries(onEachFeature: Function, params = {}, style?) {
    this._sites_group_service
      .get_geometries(params)
      .subscribe((data: GeoJSON.FeatureCollection) => {
        this.geojsonSitesGroups = data;
        this.removeSitesGroupLayerGroup();
        this.sitesGroupFeatureGroup = this.setMapData(
          data,
          onEachFeature,
          style || defaultSiteGroupStyle,
          false
        );
      });
  }

  getSitesGroupsChildGeometries(onEachFeature: Function, params = {}, style?) {
    this._sites_service.get_geometries(params).subscribe((data: GeoJSON.FeatureCollection) => {
      this.removeSitesLayerGroup();
      this.sitesLayerGroup = this.setMapData(data, onEachFeature, style);
    });
  }

  setGeomSiteGroupFromExistingObject(geom) {
    this.sitesGroupFeatureGroup = this.setMapData(geom, () => {}, undefined, false);
  }

  setMapData(
    geojson: GeoJSON.Geometry | GeoJSON.FeatureCollection,
    onEachFeature: Function,
    style?,
    enableClustering: boolean = this._configService.enableClustering
  ): L.FeatureGroup | L.MarkerClusterGroup | undefined {
    const map = this._mapService.getMap();
    if (!geojson || !geojson['features']) return;

    const layer: L.GeoJSON = this._mapService.createGeojson(geojson, false, onEachFeature, style);
    if (enableClustering) {
      const clusterGroup = this._createMarkerClusterGroup();
      const mixedGroup = new L.FeatureGroup();
      let hasClusterLayer = false;
      let hasNonClusterLayer = false;
      layer.eachLayer((geoLayer) => {
        if (geoLayer instanceof L.Marker || geoLayer instanceof L.CircleMarker) {
          clusterGroup.addLayer(geoLayer);
          hasClusterLayer = true;
          return;
        }
        mixedGroup.addLayer(geoLayer);
        hasNonClusterLayer = true;
      });

      if (hasClusterLayer) {
        mixedGroup.addLayer(clusterGroup);
      }
      this.sitesLayerGroup = hasClusterLayer && !hasNonClusterLayer ? clusterGroup : mixedGroup;

      if (this.sitesLayerGroup.getLayers().length > 0) {
        this._mapService.map.addLayer(this.sitesLayerGroup);
        map.fitBounds(this.sitesLayerGroup.getBounds());
      }
    } else {
      this.sitesLayerGroup = new L.FeatureGroup();
      this.sitesLayerGroup.addLayer(layer);
      this._mapService.map.addLayer(this.sitesLayerGroup);
      map.fitBounds(this.sitesLayerGroup.getBounds());
    }

    return this.sitesLayerGroup;
  }

  setMapDataWithFeatureGroup(featureGroup: L.LayerGroup[]) {
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
    this.setMapData(geom, () => {});
  }

  removeLayerGroup(feature: L.LayerGroup) {
    if (feature && this._mapService.map) {
      this._mapService.map.removeLayer(feature);
    }
  }

  removeSitesLayerGroup() {
    this.removeLayerGroup(this.sitesLayerGroup);
  }

  removeSitesGroupLayerGroup() {
    this.removeLayerGroup(this.sitesGroupFeatureGroup);
  }

  onEachFeature() {}

  filterSitesGroups(siteGroupId: number) {
    if (this.geojsonSitesGroups !== undefined) {
      const features = this.geojsonSitesGroups.features.filter(
        (feature) => feature.properties.id_sites_group == siteGroupId
      );
      this.geojsonSitesGroups.features = features;
      this.removeLayerGroup(this.sitesGroupFeatureGroup);
      this.setMapData(this.geojsonSitesGroups, this.onEachFeature, defaultSiteGroupStyle, false);
    }
  }

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
    this.removeLayerGroup(layers);
  }

  selectSitesLayer(id: number, zoom: boolean): L.FeatureGroup | null {
    let foundLayer: L.FeatureGroup | null = null;

    const trySelect = (layer: any, getLatLng?: () => L.LatLng) => {
      const feature = layer.feature as GeoJSON.Feature;
      if (feature.properties['id_base_site'] == id) {
        if (zoom) {
          if (getLatLng) {
            this._mapService.map.setView(getLatLng(), 18);
          } else {
            const fg = new L.FeatureGroup([layer]);
            this._mapService.map.fitBounds(fg.getBounds());
          }
        }
        layer.openPopup();
        foundLayer = new L.FeatureGroup([layer]);
      }
    };

    if (this.sitesLayerGroup) {
      if (this.sitesLayerGroup instanceof L.MarkerClusterGroup) {
        this.sitesLayerGroup.getAllChildMarkers().forEach((marker: any) => {
          if (foundLayer) return;
          trySelect(marker, () => marker.getLatLng());
        });
      } else {
        this.sitesLayerGroup.eachLayer((layer: any) => {
          if (foundLayer) return;

          if (layer instanceof L.GeoJSON) {
            layer.eachLayer((sublayer: any) => {
              if (foundLayer) return;
              trySelect(sublayer);
            });
            return;
          }

          if (layer instanceof L.MarkerClusterGroup) {
            layer.getAllChildMarkers().forEach((marker: any) => {
              if (foundLayer) return;
              trySelect(marker, () => marker.getLatLng());
            });
            return;
          }

          if (layer instanceof L.Marker || layer instanceof L.CircleMarker) {
            trySelect(layer, () => layer.getLatLng());
            return;
          }

          trySelect(layer);
        });
      }
    }

    return foundLayer;
  }

  removeAllFeatureGroup() {
    let listFeatureGroup: L.LayerGroup[] = [];
    if (!this._mapService.map) {
      return;
    }
    this._mapService.map.eachLayer(function (layer: L.LayerGroup) {
      if (layer instanceof L.FeatureGroup || layer instanceof L.MarkerClusterGroup) {
        listFeatureGroup.push(layer);
      }
    });
    for (const featureGroup of listFeatureGroup) {
      this.removeLayerGroup(featureGroup);
    }
  }

  removeFileLayerGroup() {
    this._mapService.removeAllLayers(this._mapService.map, this._mapService.fileLayerFeatureGroup);
  }

  clusterCountOverrideFn(cluster) {
    const obsChildCount = cluster.getChildCount();
    const clusterSize = obsChildCount > 100 ? 'large' : obsChildCount > 10 ? 'medium' : 'small';
    return L.divIcon({
      html: `<div><span>${obsChildCount}</span></div>`,
      className: `marker-cluster marker-cluster-${clusterSize}`,
      iconSize: L.point(40, 40),
    });
  }

  private _createSitesLayerGroup(): L.FeatureGroup | L.MarkerClusterGroup {
    return this._configService.enableClustering
      ? this._createMarkerClusterGroup()
      : new L.FeatureGroup();
  }

  private _createMarkerClusterGroup(): L.MarkerClusterGroup {
    return L.markerClusterGroup({
      disableClusteringAtZoom: 18,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: true,
      zoomToBoundsOnClick: true,
      maxClusterRadius: (zoom) => {
        if (zoom >= 15) return 50;
        if (zoom >= 12) return 100;
        return 200;
      },
      iconCreateFunction: this.clusterCountOverrideFn,
    });
  }
}
