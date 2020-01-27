import { DataMonitoringObjectService } from './../../services/data-monitoring-object.service';
import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { ConfigService } from '../../services/config.service';

import { MonitoringObject } from '../../class/monitoring-object';

import { Utils } from '../../utils/utils';

@Component({
  selector: 'pnx-monitoring-lists',
  templateUrl: './monitoring-lists.component.html',
  styleUrls: ['./monitoring-lists.component.css']
})
export class MonitoringListComponent implements OnInit {

  @Input() obj: MonitoringObject;

  @Output() bEditChanged = new EventEmitter<boolean>();

  @Input() currentUser;


  frontendModuleMonitoringUrl;
  backendUrl: string;

  children0Array = [];

  childrenDataTable;
  tempChildrenRows;
  childrenColumns;

  medias;

  @Input() objectsStatus: Object;
  @Output() objectsStatusChange: EventEmitter<Object> = new EventEmitter<Object>();

  constructor(
    private _configService: ConfigService,
  ) { }

  ngOnInit() {
    this._configService.init(this.obj.modulePath)
      .subscribe(() => {
        this.initDataTable();
      });
  }

  initDataTable() {
    this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
    this.backendUrl = this._configService.backendUrl();

    this.children0Array = this.obj.children0Array();
    // datatable
    this.childrenDataTable = this.obj.childrenColumnsAndRows('display_list');

    this.medias = this.obj.children['media'] && this.obj.children['media'].map(e => e.properties);
  }

  onSelectedChildren(typeObject, event) {
    this.objectsStatus[typeObject] = event;
    if (typeObject === 'site') {
      this.objectsStatusChange.emit(Utils.copy(this.objectsStatus));
    }
  }

  onbEditChanged(event) {
    this.bEditChanged.emit(event);
  }

  ngOnChanges(changes: SimpleChanges) {
    for (const propName of Object.keys(changes)) {
      const chng = changes[propName];
      const cur = chng.currentValue;
      const prev = chng.previousValue;
      switch (propName) {
        case 'obj':
          this.initDataTable();
          break;
      }
    }
  }
}
