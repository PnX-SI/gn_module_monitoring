import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { Subscription } from 'rxjs';
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
  private currentEditModeSubscription: Subscription;
  // search bar default to true

  @Output() onChange = new EventEmitter<any>();
  @Output() onDelete = new EventEmitter<any>();

  @Input() bZoomOnPoint = true;
  @Input() zoomLevelOnPoint = 8;

  // TODO supprimer input quand monitoring-objet n'est plus utilisé
  @Input() bEdit: boolean = false;

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

    this.currentEditModeSubscription = this._formService.currentEditMode.subscribe(
      (editMode: boolean) => {
        this.bEdit = editMode;
        this.initForm();
      }
    );
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

  ngOnChanges(changes: SimpleChanges) {
    if (changes.parentFormControl) {
      if (changes.parentFormControl.currentValue) {
        this.initForm();
      }
    }
  }
  ngOnDestroy() {
    this.currentEditModeSubscription.unsubscribe();
  }
}
