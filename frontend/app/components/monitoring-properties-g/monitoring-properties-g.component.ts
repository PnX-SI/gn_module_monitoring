import { Component, EventEmitter, Input, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Subscription } from 'rxjs';

import { ISitesGroup } from '../../interfaces/geom';
import { IobjObs, ObjDataType } from '../../interfaces/objObs';
import { FormService } from '../../services/form.service';
import { ObjectService } from '../../services/object.service';
import { JsonData } from '../../types/jsondata';

@Component({
  selector: 'pnx-monitoring-properties-g',
  templateUrl: './monitoring-properties-g.component.html',
  styleUrls: ['./monitoring-properties-g.component.css'],
})
export class MonitoringPropertiesGComponent implements OnInit {
  // selectedObj: ISitesGroup;
  @Input() selectedObj: ObjDataType;
  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();
  objectType: IobjObs<ObjDataType>;

  @Input() newParentType;
  color: string = 'white';
  dataDetails: ISitesGroup;
  fields: JsonData;
  fieldDefinitions: JsonData = {};
  fieldsNames: string[];
  endPoint: string;
  datasetForm = new FormControl();
  _sub: Subscription;

  constructor(private _formService: FormService, private _objService: ObjectService) {}

  ngOnInit() {
    this.initProperties();
  }

  initProperties() {
    this.objectType = this.newParentType;
    this.fieldsNames = this.newParentType.template.fieldNames;
    this.fields = this.newParentType.template.fieldLabels;
    this.fieldDefinitions = this.newParentType.template.fieldDefinitions;
    this.objectType.properties = this.selectedObj;
    this.endPoint = this.newParentType.endPoint;
  }

  onEditClick() {
    this.selectedObj['id'] = this.selectedObj[this.selectedObj.pk];
    this._formService.changeDataSub(
      this.selectedObj,
      this.objectType.objectType,
      this.objectType.endPoint
    );
    this.bEditChange.emit(true);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.newParentType.template.fieldNames.length != 0) {
      this.initProperties();
    }
  }
}
