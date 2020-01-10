import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  SimpleChanges
} from "@angular/core";

import { FormGroup } from "@angular/forms";
import { MonitoringObject } from "../../class/monitoring-object";
import { Layer } from "@librairies/leaflet";
import { ConfigService } from "../../services/config.service";
import { DataMonitoringObjectService } from "../../services/data-monitoring-object.service";

import { MapService } from "@geonature_common/map/map.service";

@Component({
  selector: "pnx-monitoring-map",
  templateUrl: "./monitoring-map.component.html",
  styleUrls: ["./monitoring-map.component.css"]
})
export class MonitoringMapComponent implements OnInit {
  @Input() bEdit: boolean;
  @Input() obj: MonitoringObject;

  @Input() childrenStatus: Object = {};

  @Input() childrenTypeStatus;
  @Output() childrenTypeStatusChange = new EventEmitter<Object>();

  @Input() objForm: FormGroup;

  childrenGeometries = {};
  sibblingGeometries;
  childrenTypes = [];

  // todo mettre en config
  styleConfig = {
    edit: {
      opacity: 0.2,
      fillOpacity: 0.1
    },
    hidden: {
      opacity: 0,
      fillOpacity: 0
    },
    sibbling: {
      opacity: 0.5,
      fillOpacity: 0.3
    },
    parent: {
      opacity: 0.3,
      fillOpacity: 0.2
    },
    object: {
      opacity: 0.8,
      fillOpacity: 0.5
    },
    normal: {
      opacity: 0.7,
      fillOpacity: 0.5
    }
  };

  constructor(
    private _mapService: MapService,
    private _configService: ConfigService
  ) {}

  ngOnInit() {
    this.sibblingGeometries = this.obj.sibblingGeometries();
    this.childrenTypes = this.obj.childrenTypes("geometry_type");
    this.childrenGeometries = this.obj.childrenGeometries();

    let childrenGeometries = this.childrenGeometries;

      this.objForm.valueChanges.subscribe((change) => {
          if(change['code_circuit_point']) {
            let layer = this.findObjectLayer('circuit_point',change['code_circuit_point'], 'base_site_code')            
            layer && layer.openPopup();
          }
        });

    setTimeout(() => {
      if (this.obj.isObservationCircuit()) {
        let $this = this;
        this.obj.circuitPoints.features.forEach(p => {
          $this.setPopup(p.object_type, p.id);
          let layer: Layer = $this.findObjectLayer("circuit_point", p.id);
          
          let val  = layer['feature'].properties.base_site_code;
          
          if($this.obj.properties['code_circuit_point'] == val) {
            layer.openPopup();
            layer['setStyle']({'color': 'red'})
          }
          
          layer.on('click', (e) => {
            let val  = e.target.feature.properties.base_site_code;  
            $this.objForm.patchValue({'code_circuit_point': val})
          });


        });
      }

      let $this = this;
      this.childrenTypes.forEach(childrenType => {
        if (childrenGeometries[childrenType]) {
          childrenGeometries[childrenType].features.forEach(geom => {
            $this.setPopup(geom.object_type, geom.id);
          });
        }
      });
    }, 500);
  }

  styleObject(typeStyle, bEdit = false) {
    // return null;
    // return this.styleConfig['normal']
    // return this.bEdit && this.styleConfig['edit'] || this.styleConfig[typeStyle] || {
    //   opacity: 0.7,
    //   fillOpacity: 0.5,
    //   color: 'lightblue'
    // };
  }

  findObjectLayer(objectType, fieldValue, fieldName='id'): Layer {
    let layers = this._mapService.map["_layers"];
    let layerKey = Object.keys(layers).find(key => {
      let feature = layers[key] && layers[key].feature;
      return feature && (feature[fieldName] == fieldValue || feature.properties[fieldName] == fieldValue) && feature.object_type == objectType;
    });
    return layerKey && layers[layerKey];
  }

  setPopup(objectType, id) {
    let layer = this.findObjectLayer(objectType, id);

    let ObjectLabel = this._configService.configModuleObjectParam(
      "objects",
      this.obj.modulePath,
      layer['feature'].object_type,
      "label"
    );

    let sPopup = `
    <div>
      ${ObjectLabel} ${layer['feature'].properties.description || layer['feature'].properties.base_site_name}
    </div>    
    `;

    layer.bindPopup(sPopup).closePopup();
  }

  setObjectLayerStyle(objectType, id, status) {
    let layer = this.findObjectLayer(objectType, id);
    if (!layer) return;

    let style = status.visible
      ? this.styleConfig.normal
      // ? this.styleObject('normal', this.bEdit)
      : this.styleConfig.hidden;
    layer['setStyle'](style);

    if (status.selected) {
      layer.openPopup();
    }

    if (!status.visible || !status.selected) {
      layer.closePopup();
    }
  }

  setSelectedChildrenGeometries() {
    this.childrenTypes.forEach(childrenType => {
      this.setSelectedChildrenGeometriesOfType(childrenType);
    });
  }

  setSelectedChildrenGeometriesOfType(childrenType) {
    if (
      !(this._mapService.map && this._mapService.map["_layers"]) &&
      this.childrenTypeStatusChange[childrenType]
    ) {
      return;
    }
    this.childrenStatus[childrenType].forEach(status => {
      this.setObjectLayerStyle(childrenType, status.id, status);
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    for (let propName in changes) {
      let chng = changes[propName];
      let cur = chng.currentValue;
      let prev = chng.previousValue;
      switch (propName) {
        case "childrenTypeStatus":
          cur && this.setSelectedChildrenGeometriesOfType(cur);
      }
    }
  }
}
