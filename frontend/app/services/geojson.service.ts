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
};

@Injectable()
export class GeoJSONService {
  geojsonSitesGroups: GeoJSON.FeatureCollection;
  geojsonSites: GeoJSON.FeatureCollection;
  sitesGroupFeatureGroup: L.FeatureGroup;
  sitesFeatureGroup: L.FeatureGroup;
  currentLayer: any = null;

  extraLayers: Object = {};

  constructor(
    private _sites_group_service: SitesGroupService,
    private _sites_service: SitesService,
    private _mapService: MapService,
    private _formService: FormService
  ) {}

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
    params = {},
    sitesGroupstyle?,
    sitesStyle?
  ) {
    return forkJoin({
      sitesGroup: this._sites_group_service.get_geometries(params),
      sites: this._sites_service.get_geometries(params),
    }).subscribe((data) => {
      this.geojsonSitesGroups = data['sitesGroup'];
      this.removeFeatureGroup(this.sitesGroupFeatureGroup);
      this.sitesGroupFeatureGroup = this.setMapData(
        data['sitesGroup'],
        sitesGroupOnEachFeature,
        sitesGroupstyle || defaultSiteGroupStyle
      );
      this.removeFeatureGroup(this.sitesFeatureGroup);
      this.sitesFeatureGroup = this.setMapData(data['sites'], sitesOnEachFeature, sitesStyle);
    });
  }

  getSitesGroupsGeometries(onEachFeature: Function, params = {}, style?) {
    this._sites_group_service
      .get_geometries(params)
      .subscribe((data: GeoJSON.FeatureCollection) => {
        this.geojsonSitesGroups = data;
        this.removeFeatureGroup(this.sitesGroupFeatureGroup);
        this.sitesGroupFeatureGroup = this.setMapData(
          data,
          onEachFeature,
          style || defaultSiteGroupStyle
        );
      });
  }

  getSitesGroupsChildGeometries(onEachFeature: Function, params = {}, style?) {
    this._sites_service.get_geometries(params).subscribe((data: GeoJSON.FeatureCollection) => {
      this.removeFeatureGroup(this.sitesFeatureGroup);
      this.sitesFeatureGroup = this.setMapData(data, onEachFeature, style);
    });
  }

  setGeomSiteGroupFromExistingObject(geom) {
    this.sitesGroupFeatureGroup = this.setMapData(geom, () => {});
  }

  setMapData(
    geojson: GeoJSON.Geometry | GeoJSON.FeatureCollection,
    onEachFeature: Function,
    style?
  ) {
    const map = this._mapService.getMap();
    const layer: L.Layer = this._mapService.createGeojson(geojson, false, onEachFeature, style);
    const featureGroup = new L.FeatureGroup();
    this._mapService.map.addLayer(featureGroup);
    featureGroup.addLayer(layer);
    map.fitBounds(featureGroup.getBounds());

    return featureGroup;
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
    if (feature) {
      this._mapService.map.removeLayer(feature);
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
    this._mapService.map.eachLayer(function (layer) {
      if (layer instanceof L.FeatureGroup) {
        listFeatureGroup.push(layer);
      }
    });
    for (const featureGroup of listFeatureGroup) {
      this.removeFeatureGroup(featureGroup);
    }
  }
}
