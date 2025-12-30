import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { FormControl } from '@angular/forms';
import { distinctUntilChanged } from 'rxjs/operators';
import { isEqual } from 'lodash';
import { leafletDrawOptions } from './leaflet-draw.options';
import { CustomMarkerIcon } from '@geonature_common/map/marker/marker.component';
import { FormService } from '../../services/form.service';
import { IFormMap } from '../../interfaces/object';

@Component({
  selector: 'pnx-draw-form',
  templateUrl: './draw-form.component.html',
  styleUrls: ['./draw-form.component.css'],
})
export class DrawFormComponent implements OnInit {
  public geojson;
  public leafletDrawOptions: any;

  public parentFormControl: FormControl;
  /** Type de geomtrie parmi : 'Point', 'Polygon', 'LineString' */
  public geometryType: string[] = [];

  // search bar default to true

  @Output() onChange = new EventEmitter<any>();
  @Output() onDelete = new EventEmitter<any>();

  @Input() bZoomOnPoint = true;
  @Input() zoomLevelOnPoint = 8;

  @Input() bEdit;

  @Input() geomFromProtocol: boolean = true;

  constructor(private _formService: FormService) {}

  ngOnInit() {
    this._formService.currentFormMap
      .pipe(distinctUntilChanged((prev, curr) => prev.frmGp === curr.frmGp))
      .subscribe((formMapObj: IFormMap) => {
        if (!formMapObj || !formMapObj.frmGp) {
          return;
        }
        this.geometryType = formMapObj.geometry_type;
        this.parentFormControl = formMapObj.frmGp;
        this.initForm();
      });
    // choix du type de geometrie
    this.initDrawConfig();
  }

  initForm() {
    if (!(this.geometryType && this.parentFormControl)) {
      return;
    }
    if (this.bEdit === false) {
      return;
    }
    this.initDrawConfig();
    if (this.geometryType.includes('Point')) {
      this.leafletDrawOptions.draw.marker = {
        icon: new CustomMarkerIcon(),
      };
    }
    if (this.geometryType.includes('Polygon')) {
      this.leafletDrawOptions.draw.polygon = {
        allowIntersection: false, // Restricts shapes to simple polygons
        drawError: {
          color: '#e1e100', // Color the shape will turn when intersects
          message: 'Intersection forbidden !', // Message that will show when intersect
        },
      };
    }
    if (this.geometryType.includes('LineString')) {
      this.leafletDrawOptions.draw.polyline = true;
    }
    // default if not specified
    if (
      !this.geometryType.includes('Point') &&
      !this.geometryType.includes('LineString') &&
      !this.geometryType.includes('Polygon')
    ) {
      this.leafletDrawOptions.draw.marker = {
        icon: new CustomMarkerIcon(),
      };
    }

    this.leafletDrawOptions = { ...this.leafletDrawOptions };
    if (this.parentFormControl && this.parentFormControl.value) {
      // init geometry from parentFormControl
      this.setGeojson(this.parentFormControl.value);
    }
  }

  initDrawConfig() {
    this.leafletDrawOptions = JSON.parse(JSON.stringify(leafletDrawOptions));
  }

  setGeojson(geometry: JSON) {
    this.geojson = geometry;
  }

  // suivi composant => formControl
  bindGeojsonForm(geojson: JSON) {
    this.manageGeometryChange(geojson);
  }

  manageGeometryChange(geometry: JSON) {
    if (!isEqual(geometry, this.parentFormControl.value)) {
      this.parentFormControl.setValue(geometry);
    }
  }

  cleanControl() {
    /**
     * PATCH en attendant l'intégration de la PR https://github.com/PnX-SI/GeoNature/pull/3842
     * qui sera incluse dans la version 2.17 de GeoNature
     * Si on passe en mode non-édition, on supprime les contrôles Leaflet Draw (boutons)
     */
    if (this.bEdit === false) {
      const currentGpsElement: HTMLCollection = document.getElementsByClassName(
        'leaflet-bar leaflet-control leaflet-control-custom'
      );
      for (let c of <any>currentGpsElement) {
        c.remove();
      }
      const currentfileLayer: HTMLCollection = document.getElementsByClassName(
        'leaflet-control-filelayer leaflet-control-zoom leaflet-bar leaflet-control'
      );
      for (let c of <any>currentfileLayer) {
        c.remove();
      }
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.parentFormControl) {
      if (changes.parentFormControl.currentValue) {
        this.initForm();
      }
    }

    /**
     * PATCH en attendant l'intégration de la PR https://github.com/PnX-SI/GeoNature/pull/3842
     * qui sera incluse dans la version 2.17 de GeoNature
     * */
    if (changes.bEdit && !changes.bEdit.firstChange) {
      this.cleanControl();
      this.initForm();
    }
  }
}
