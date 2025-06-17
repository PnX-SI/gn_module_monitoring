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
  sitesFeatureGroup: L.FeatureGroup;
  currentLayer: any = null;
  markerClusterGroup: L.MarkerClusterGroup; 

  constructor(
    private _sites_group_service: SitesGroupService,
    private _sites_service: SitesService,
    private _mapService: MapService,
    private _formService: FormService
  ) {
    this.markerClusterGroup = L.markerClusterGroup({
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

  removeAllLayers() {
    this.removeFeatureGroup(this.sitesGroupFeatureGroup);
    this.removeFeatureGroup(this.sitesFeatureGroup);
    this.removeClusterGroup(this.markerClusterGroup); 
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
    sitesStyle?,
    enableCluster = false
  ) {
    return forkJoin({
      sitesGroup: this._sites_group_service.get_geometries(paramsSitesGroup),
      sites: this._sites_service.get_geometries(paramsSite),
    }).subscribe((data) => {
      this.geojsonSitesGroups = data['sitesGroup'];
      this.removeFeatureGroup(this.sitesGroupFeatureGroup);
      this.sitesGroupFeatureGroup = this.setMapData(
        data['sitesGroup'],
        sitesGroupOnEachFeature,
        sitesGroupstyle || defaultSiteGroupStyle,
      );
      this.removeFeatureGroup(this.sitesFeatureGroup);
      this.sitesFeatureGroup = this.setMapData(data['sites'], sitesOnEachFeature, sitesStyle, enableCluster);
    });
  }

  getSitesGroupsGeometries(onEachFeature: Function, params = {}, style?, enableCluster = false) {
    this._sites_group_service
      .get_geometries(params)
      .subscribe((data: GeoJSON.FeatureCollection) => {
        this.geojsonSitesGroups = data;
        this.removeFeatureGroup(this.sitesGroupFeatureGroup);
        this.sitesGroupFeatureGroup = this.setMapData(
          data,
          onEachFeature,
          style || defaultSiteGroupStyle,
          enableCluster
        );
      });
  }

  getSitesGroupsChildGeometries(onEachFeature: Function, params = {}, style?, enableCluster = false) {
    this._sites_service.get_geometries(params).subscribe((data: GeoJSON.FeatureCollection) => {
      this.removeFeatureGroup(this.sitesFeatureGroup);
      this.sitesFeatureGroup = this.setMapData(data, onEachFeature, style, enableCluster);
    });
  }

  setGeomSiteGroupFromExistingObject(geom) {
    this.sitesGroupFeatureGroup = this.setMapData(geom, () => {});
  }

  setMapData(
    geojson: GeoJSON.Geometry | GeoJSON.FeatureCollection,
    onEachFeature: Function,
    style?,
    enableCluster = false
  ): L.FeatureGroup | undefined {
    const map = this._mapService.getMap();
    if (!geojson || !geojson['features']) return;
  
    const layer: L.GeoJSON = this._mapService.createGeojson(geojson, false, onEachFeature, style);
    const featureGroup = new L.FeatureGroup();
  
    if (enableCluster) {
      this._handleClustering(layer, featureGroup);
    } else {
      this._addToFeatureGroup(layer, featureGroup);
      this._addLayerToMap(featureGroup);
      map.fitBounds(featureGroup.getBounds());
    }
  
    return featureGroup;
  }

  private _handleClustering(layer: L.GeoJSON, fallbackGroup: L.FeatureGroup): void {
    layer.eachLayer((geoLayer) => {
      if (geoLayer instanceof L.Marker || geoLayer instanceof L.CircleMarker) {
        const feature = (geoLayer as any).feature;
        const popupContent = feature?.properties?.base_site_name || '';
        geoLayer.bindPopup(popupContent);
        this.markerClusterGroup.addLayer(geoLayer);
      } else {
        fallbackGroup.addLayer(geoLayer);
      }
    });
  
    if (this.markerClusterGroup.getLayers().length > 0) {
      this._addLayerToMap(this.markerClusterGroup);
      this._mapService.map.fitBounds(this.markerClusterGroup.getBounds());
    }
  
    if (fallbackGroup.getLayers().length > 0) {
      this._addLayerToMap(fallbackGroup);
    }
  }
  
  private _addToFeatureGroup(layer: L.GeoJSON, featureGroup: L.FeatureGroup): void {
    layer.eachLayer((geoLayer) => {
      featureGroup.addLayer(geoLayer);
    });
  }
  
  private _addLayerToMap(layer: L.LayerGroup): void {
    this._mapService.map.addLayer(layer);
  }
  

  setMapDataWithFeatureGroup(featureGroup: L.FeatureGroup[]) {
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

  removeFeatureGroup(feature: L.FeatureGroup) {
    if (feature && this._mapService.map) {
      this._mapService.map.removeLayer(feature);
    }
  }

  removeClusterGroup(feature: L.MarkerClusterGroup) {
    if (feature && this._mapService.map) {
      this._mapService.map.removeLayer(this.markerClusterGroup);
      this.markerClusterGroup.clearLayers()
    }
  }

  onEachFeature() {}

  filterSitesGroups(siteGroupId: number) {
    if (this.geojsonSitesGroups !== undefined) {
      const features = this.geojsonSitesGroups.features.filter(
        (feature) => feature.properties.id_sites_group == siteGroupId
      );
      this.geojsonSitesGroups.features = features;
      this.removeFeatureGroup(this.sitesGroupFeatureGroup);
      this.setMapData(this.geojsonSitesGroups, this.onEachFeature, defaultSiteGroupStyle);
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
    this.removeFeatureGroup(layers);
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
  
    // Recherche dans sitesFeatureGroup
    this.sitesFeatureGroup?.eachLayer((layer: any) => {
      if (foundLayer) return;
  
      if (layer instanceof L.GeoJSON) {
        layer.eachLayer((sublayer: any) => {
          if (foundLayer) return;
          trySelect(sublayer);
        });
      } else {
        trySelect(layer);
      }
    });
  
    // Recherche dans le cluster
    if (!foundLayer && this.markerClusterGroup) {
      this.markerClusterGroup.eachLayer((layer: any) => {
        if (foundLayer) return;
        trySelect(layer, () => layer.getLatLng());
      });
    }
  
    return foundLayer;
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
    }
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
}
