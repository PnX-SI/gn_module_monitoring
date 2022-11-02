import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  ViewEncapsulation,
} from "@angular/core";
import { FormControl, FormGroup } from "@angular/forms";

import { leafletDrawOptions } from "./leaflet-draw.options";
import { CustomMarkerIcon } from "@geonature_common/map/marker/marker.component";

@Component({
  selector: "pnx-draw-form",
  templateUrl: "./draw-form.component.html",
  styleUrls: ["./draw-form.component.css"],
})
export class DrawFormComponent implements OnInit {
  public geojson;
  public leafletDrawOptions = leafletDrawOptions;
  formValueChangeSubscription;

  public displayed = false;

  @Input() parentFormControl: FormControl;
  /** Type de geomtrie parmi : 'Point', 'Polygon', 'LineString' */
  @Input() geometryType: string;

  // search bar default to true

  @Output() onChange = new EventEmitter<any>();
  @Output() onDelete = new EventEmitter<any>();

  @Input() bZoomOnPoint = true;
  @Input() zoomLevelOnPoint = 8;

  @Input() bEdit;

  constructor() {}

  ngOnInit() {
    // choix du type de geometrie

    this.initForm();
  }

  initForm() {
    if (!(this.geometryType && this.parentFormControl)) {
      // on cache
      this.displayed = false;
      return;
    }

    this.displayed = true;
    switch (this.geometryType) {
      case "Point": {
        this.leafletDrawOptions.draw.marker = {
          icon: new CustomMarkerIcon(),
        };
        break;
      }
      case "Polygon": {
        this.leafletDrawOptions.draw.polygon = {
          allowIntersection: false, // Restricts shapes to simple polygons
          drawError: {
            color: "#e1e100", // Color the shape will turn when intersects
            message: "Intersection forbidden !", // Message that will show when intersect
          },
        };
        break;
      }
      case "LineString": {
        this.leafletDrawOptions.draw.polyline = true;
        break;
      }
      default: {
        this.leafletDrawOptions.draw.marker = true;
        break;
      }
    }

    this.leafletDrawOptions = { ...this.leafletDrawOptions };

    if (this.formValueChangeSubscription) {
      this.formValueChangeSubscription.unsubscribe();
    }
    if (this.parentFormControl && this.parentFormControl.value) {
      // init geometry from parentFormControl
      this.setGeojson(this.parentFormControl.value);
      // suivi formControl => composant
      this.formValueChangeSubscription =
        this.parentFormControl.valueChanges.subscribe((geometry) => {
          this.setGeojson(geometry);
        });
    }
  }

  setGeojson(geometry) {
    setTimeout(() => {
      this.geojson = { geometry: geometry };
    });
  }

  // suivi composant => formControl
  bindGeojsonForm(geojson) {
    this.geojson = geojson;
    this.parentFormControl.setValue(geojson.geometry);
  }

  ngOnChanges(changes) {
    if (changes.parentFormControl && changes.parentFormControl.currentValue) {
      this.initForm();
    }
    if (changes.geometryType && changes.geometryType.currentValue) {
      this.initForm();
    }
  }
}
