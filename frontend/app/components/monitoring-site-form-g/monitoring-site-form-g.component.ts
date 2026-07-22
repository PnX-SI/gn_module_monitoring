import { Component, OnInit, Input, AfterViewInit, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators, FormControl, FormArray } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { MonitoringFormGComponent } from '../monitoring-form-g/monitoring-form-g.component';
import { CommonService } from '@geonature_common/service/common.service';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';
import { Location } from '@angular/common';
import { FormService } from '../../services/form.service';
import { DataUtilsService } from '../../services/data-utils.service';
import { JsonData } from '../../types/jsondata';
import { GeoJSONService } from '../../services/geojson.service';
import { NavigationService } from '../../services/navigation.service';

@Component({
  selector: 'pnx-monitoring-site-form-g',
  templateUrl: './monitoring-site-form-g.component.html',
  styleUrls: ['./monitoring-site-form-g.component.css'],
})
export class MonitoringSiteFormGComponent extends MonitoringFormGComponent {
  constructor(
    _commonService: CommonService,
    _formService: FormService,
    _dataUtilsService: DataUtilsService,
    _dynformService: DynamicFormService,
    _formBuilder: FormBuilder,
    _location: Location,
    _geojsonService: GeoJSONService,
    _navigationService: NavigationService,
    _route: ActivatedRoute
  ) {
    super(
      _commonService,
      _formService,
      _dataUtilsService,
      _dynformService,
      _formBuilder,
      _location,
      _geojsonService,
      _navigationService,
      _route
    );
  }
}
