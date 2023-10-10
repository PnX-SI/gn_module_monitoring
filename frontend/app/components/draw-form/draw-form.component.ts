import { Component, OnInit, Input, Output, EventEmitter, ViewEncapsulation } from '@angular/core';
import { FormControl } from '@angular/forms';
import { isEqual } from 'lodash';
import { leafletDrawOptions } from './leaflet-draw.options';
import { CustomMarkerIcon } from '@geonature_common/map/marker/marker.component';
import { FormService } from '../../services/form.service';
import { GeoJSONService } from '../../services/geojson.service';

@Component({
  selector: 'pnx-draw-form',
  templateUrl: './draw-form.component.html',
  styleUrls: ['./draw-form.component.css'],
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

  constructor(
    private _formService: FormService,
    public geoJsonService: GeoJSONService
  ) {}

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
      case 'Point': {
        this.leafletDrawOptions.draw.polygon = false;
        this.leafletDrawOptions.draw.marker = {
          icon: new CustomMarkerIcon(),
        };
        break;
      }
      case 'Polygon': {
        this.leafletDrawOptions.draw.marker = false;
        this.leafletDrawOptions.draw.polygon = {
          allowIntersection: false, // Restricts shapes to simple polygons
          drawError: {
            color: '#e1e100', // Color the shape will turn when intersects
            message: 'Intersection forbidden !', // Message that will show when intersect
          },
        };
        break;
      }
      case 'LineString': {
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
      console.log(this.parentFormControl)
      // init geometry from parentFormControl
      this.setGeojson(this.parentFormControl.value);
      // suivi formControl => composant
      // this.formValueChangeSubscription = this.parentFormControl.valueChanges.subscribe(
      //   (geometry) => {
      //     this.setGeojson(geometry);
      //   }
      // );
    }
  }

  setGeojson(geometry) {
    setTimeout(() => {
      this.geojson = { geometry: geometry };
    });
  }

  // suivi composant => formControl
  bindGeojsonForm(geojson) {
    if (!this.parentFormControl) {
      this._formService.currentFormMap.subscribe((dataForm) => {
        if ('geometry' in dataForm.frmGp.controls) {
          this.parentFormControl = dataForm.frmGp.controls['geometry'] as FormControl;
          // this.parentFormControl.setValue(geojson.geometry);
          this.manageGeometryChange(geojson.geometry);
        }
      });
    } else {
      this.manageGeometryChange(geojson.geometry);
      // this.parentFormControl.setValue(geojson.geometry);
    }
  }

  manageGeometryChange(geometry) {
    if (!isEqual(geometry, this.parentFormControl.value)) {
      this.parentFormControl.setValue(geometry);
    }
  }

  ngOnChanges(changes) {
    if (changes.parentFormControl && changes.parentFormControl.currentValue) {
      this.initForm();
    }
    // if (changes.geometryType && changes.geometryType.currentValue) {
    //   console.log("ICI changement draw form parentFormControl et geometryType")
    //   this.initForm();
    // }
  }
}
