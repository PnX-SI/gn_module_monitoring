import { Component, EventEmitter, Input, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Subscription } from 'rxjs';

import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { ISitesGroup } from '../../interfaces/geom';
import { IobjObs, ObjDataType } from '../../interfaces/objObs';
import { FormService } from '../../services/form.service';
import { ObjectService } from '../../services/object.service';
import { JsonData } from '../../types/jsondata';
import { TPermission } from '../../types/permission';
import { ObjectsPermissionMonitorings } from '../../enum/objectPermission';

@Component({
  selector: 'pnx-monitoring-properties-g',
  templateUrl: './monitoring-properties-g.component.html',
  styleUrls: ['./monitoring-properties-g.component.css'],
})
export class MonitoringPropertiesGComponent implements OnInit {
  // selectedObj: ISitesGroup;
  @Input() selectedObj: ObjDataType;
  @Input() selectedObjRaw: ObjDataType;
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

  specificFields: JsonData;
  specificFieldDefinitions: JsonData = {};
  specificFieldsNames: string[];

  @Input() permission: TPermission;

  canUpdateObj: boolean;

  toolTipNotAllowed: string;

  constructor(
    private _formService: FormService,
    private _objService: ObjectService
  ) {}

  ngOnInit() {
    this.toolTipNotAllowed = TOOLTIPMESSAGEALERT;
  }

  initProperties() {
    this.objectType = this.newParentType;
    this.fieldsNames = this.newParentType.template.fieldNames;
    this.fields = this.newParentType.template.fieldLabels;
    this.fieldDefinitions = this.newParentType.template.fieldDefinitions;
    this.objectType.properties = this.selectedObj;
    this.endPoint = this.newParentType.endPoint;
  }

  initSpecificProperties() {
    this.specificFieldsNames = this.newParentType.template_specific.fieldNames;
    this.specificFields = this.newParentType.template_specific.fieldLabels;
    this.specificFieldDefinitions = this.newParentType.template_specific.fieldDefinitions;
  }

  onEditClick() {
    this.selectedObjRaw['id'] = this.selectedObjRaw[this.selectedObjRaw.pk];
    this._formService.changeDataSub(
      this.selectedObjRaw,
      this.objectType.objectType,
      this.objectType.endPoint
    );
    this.bEditChange.emit(true);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.newParentType && this.newParentType.template.fieldNames.length != 0) {
      this.initProperties();
      if (this.selectedObj) {
        this.canUpdateObj = this.selectedObj['cruved']['U'];
      }
      if (
        this.newParentType.template_specific &&
        this.newParentType.template_specific.fieldNames &&
        this.newParentType.template_specific.fieldNames.length != 0
      ) {
        this.initSpecificProperties();
      }
    }
  }
}
