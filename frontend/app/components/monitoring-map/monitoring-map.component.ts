import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  SimpleChanges,
} from "@angular/core";

import { FormGroup } from "@angular/forms";
import { MonitoringObject } from "../../class/monitoring-object";
import { Layer, svg, Path } from "leaflet";
import { ConfigService } from "../../services/config.service";
import { DataMonitoringObjectService } from "../../services/data-monitoring-object.service";

import { MapService } from "@geonature_common/map/map.service";
import { MapListService } from "@geonature_common/map-list/map-list.service";
import { Utils } from "../../utils/utils";
import * as L from "leaflet";

@Component({
  selector: "pnx-monitoring-map",
  templateUrl: "./monitoring-map.component.html",
  styleUrls: ["./monitoring-map.component.css"],
})
export class MonitoringMapComponent implements OnInit {
  @Input() bEdit: boolean;
  @Input() obj: MonitoringObject;

  @Input() objectsStatus: Object;
  @Output() objectsStatusChange: EventEmitter<Object> =
    new EventEmitter<Object>();

  @Input() objForm: FormGroup;

  @Input() sites: {};
  @Input() sitesGroup: {};

  @Input() heightMap;

  bListen = true;
  panes = {};
  renderers = {};
  map;
  selectedSiteId: Number;
  currentSiteId: Number;
  publicDisplaySitesGroup: boolean = false;

  // Layer des contours groupes de sites
  sitesGroupEmprisePoly = [];
  sitesGroupEmpriseLabel = [];

  // todo mettre en config

  styles = {
    hidden: {
      opacity: 0,
      fillOpacity: 0,
      color: "blue",
      zIndex: 0,
    },
    default: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: "blue",
      zIndex: 600,
    },
    current: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: "green",
      zIndex: 650,
    },
    selected: {
      opacity: 0.7,
      fillOpacity: 0.5,
      color: "red",
      zIndex: 660,
    },
    edit: {
      opacity: 0.2,
      fillOpacity: 0.1,
      color: "blue",
      zIndex: 600,
    },
  };

  constructor(
    protected _mapService: MapService,
    private _configService: ConfigService,
    private _data: DataMonitoringObjectService,
    private _mapListService: MapListService
  ) {}

  ngOnInit() {}

  initSites() {
    this.removeLabels();
    const layers = this._mapService.map["_layers"];
    for (const key of Object.keys(layers)) {
      const layer = layers[key];
      try {
        layer.unbindTooltip();
      } catch {}
    }
    setTimeout(() => {
      this.initPanes();
      if (this.sites && this.sites["features"]) {
        this.initSitesStatus();
        for (const site of this.sites["features"]) {
          this.setPopup(site.id);
          const layer = this.findSiteLayer(site.id);
          // pane
          const fClick = this.onLayerClick(site);
          layer.off("click", fClick);
          layer.on("click", fClick);
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
      return;
    }
    const layers = this._mapService.map["_layers"];
    for (const key of Object.keys(layers)) {
      const layer = layers[key];
      if (layer.options.permanent) {
        layer.removeFrom(this._mapService.map);
      }
    }
  }

  onEachFeature = (feature, layer) => {
    const mapLabelFieldName = this.obj.configParam("map_label_field_name");
    if (!mapLabelFieldName) {
      return;
    }
    const textValue = feature.resolvedProperties[mapLabelFieldName];
    if (!textValue) {
      return;
    }

    let coordinates;
    if (feature.geometry.type == "Point") {
      coordinates = layer.getLatLng();
    } else {
      coordinates = layer.getBounds().getCenter();
    }

    var text = L.tooltip({
      permanent: true,
      direction: "top",
      className: "text",
    })
      .setContent(textValue)
      .setLatLng(coordinates);
    layer.bindTooltip(text).openTooltip();
    text.addTo(this._mapService.map);
  };

  onLayerClick(site) {
    return (event) => {
      const id = this.selectedSiteId === site.id ? -1 : site.id;
      this.setSelectedSite(id);
      this.bListen = false;
      this.objectsStatusChange.emit(Utils.copy(this.objectsStatus));
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

  initSitesStatus() {
    if (!this.objectsStatus["site"]) {
      this.objectsStatus["site"] = [];
    }
    const $this = this;
    this.sites["features"].forEach((site) => {
      const status = $this.objectsStatus["site"].find((s) => s.id === site.id);
      if (status) {
        return;
      }

      $this.objectsStatus["site"].push({
        selected: false,
        visible: true,
        id: site.id,
      });
    });
  }

  setSelectedSite(id) {
    if (id == this.selectedSiteId) {
      return;
    }

    // Get old select site
    let old_s_site = this.objectsStatus["site"].filter(
      (site) => site.id == this.selectedSiteId
    );
    if (old_s_site.length > 0) {
      old_s_site[0]["selected"] = false;
      this.setSiteStyle(old_s_site[0]);
    }

    // Get new select site
    let new_s_site = this.objectsStatus["site"].filter((site) => site.id == id);
    if (new_s_site.length > 0) {
      new_s_site[0]["selected"] = true;
      this.setSiteStyle(new_s_site[0]);
    }
    this.selectedSiteId = id;
  }

  setSitesStyle() {
    const objectType = this.objectsStatus["type"];
    let openPopup = true;

    if (this._mapService.map) {
      this.objectsStatus[objectType] &&
        this.objectsStatus[objectType].forEach((status) => {
          this.setSiteStyle(status, openPopup, objectType);
        });
    }
    // Si le dessin des groupes de sites est actif calcul de l'aire
    if (
      this._configService.config()[this.obj.moduleCode]["module"][
        "b_draw_sites_group"
      ]
    ) {
      this.publicDisplaySitesGroup = true;
    }
  }

  setSiteStyle(status, openPopup = true, objectType = "site") {
    /*
      Défini le style des éléments
      statuts = statut de l'élément provient de objectsStatus
      openPopup = indique si la popup doit s'afficher
    */
    const map = this._mapService.map;
    let layer = this.findSiteLayer(status.id, objectType);

    if (!layer) {
      return;
    }

    const style_name = !status["visible"]
      ? "hidden"
      : status["current"]
      ? "current"
      : status["selected"]
      ? "selected"
      : this.bEdit
      ? "edit"
      : "default";

    const style = this.styles[style_name] || this.styles["default"];

    style["pane"] = this.panes[style_name];
    style["renderer"] = this.renderers[style_name];
    // layer.removeFrom(map);
    layer.setStyle(style);
    // layer.addTo(map);

    if (status["selected"]) {
      this._mapListService.zoomOnSelectedLayer(map, layer);
    }

    if (status["selected"] && openPopup == true) {
      if (!(layer as any)._popup) {
        this.setPopup(status.id);
        layer = this.findSiteLayer(status.id, objectType);
      }
      layer.openPopup();
    }

    if (!status["visible"] || !status["selected"]) {
      layer.closePopup();
    }

    // Affichage des tooltips uniquement si la feature est visible
    if (layer.getTooltip) {
      var toolTip = layer.getTooltip();
      if (style_name == "hidden") {
        if (toolTip) {
          map.closeTooltip(toolTip);
        }
      } else {
        if (toolTip) {
          map.addLayer(toolTip);
        }
      }
    }
  }

  findSiteLayer(id, objectType = "site"): Path {
    const layers = this._mapService.map["_layers"];
    const layerKey = Object.keys(layers)
      .filter((key) => {
        const monitoringObject = layers[key] && layers[key].feature;
        return monitoringObject && monitoringObject.objectType == objectType;
      })
      .find((key) => {
        const feature = layers[key] && layers[key].feature;
        return (
          feature && (feature["id"] === id || feature.properties["id"] === id)
        );
      });
    return layerKey && layers[layerKey];
  }

  findSiteLayers(value, property): Array<Layer> {
    const layers = this._mapService.map["_layers"];

    let filterlayers = Object.keys(layers)
      .filter(
        (key) =>
          layers[key].feature &&
          layers[key]["feature"]["properties"][property] == value
      )
      .map((key) => ({ [key]: layers[key] }));

    if (filterlayers.length > 0) {
      return Object.assign(...(filterlayers as [Object]));
    }
    return [];
  }

  setPopup(id) {
    const layer = this.findSiteLayer(id);
    if (layer['_popup']) {
      return;
    }
    // TODO verifier si le fait de spécifier # en dur
    //  Ne pose pas de soucis pour certaine configuration
    const url = [
      "#",
      this._configService.frontendModuleMonitoringUrl(),
      "object",
      this.obj.moduleCode,
      "site",
      layer['feature'].properties.id_base_site,
    ].join("/");

    const sPopup = `
    <div>
      <h4>  <a href=${url}>${
      layer["feature"].properties.base_site_name
    }</a></h4>
      ${layer["feature"].properties.description || ""}
    </div>
    `;

    layer.bindPopup(sPopup).closePopup();
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
        case "objectsStatus":
          if (!this.bListen) {
            this.bListen = true;
          } else {
            this.setSitesStyle();
          }
          break;
        case "bEdit":
          this.setSitesStyle();

          break;
        case "sites":
          this.initSites();
      }
    }
  }
}
