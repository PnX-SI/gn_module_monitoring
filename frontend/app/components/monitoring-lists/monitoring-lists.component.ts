import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { ConfigService } from "../../services/config.service";

import { MonitoringObject } from '../../class/monitoring-object';

@Component({
  selector: 'pnx-monitoring-lists',
  templateUrl: './monitoring-lists.component.html',
  styleUrls: ['./monitoring-lists.component.css']
})
export class MonitoringListComponent implements OnInit {

  @Input() obj: MonitoringObject;

  frontendModuleMonitoringUrl;
  backendUrl: string;

  children0Array = [];

  childrenDataTable;
  tempChildrenRows;
  childrenColumns;

  medias;

  @Input() childrenStatus: Object = {};
  // @Output() childrenStatusChange = new EventEmitter<Object>();
  
  @Input() childrenTypeStatus;
  @Output() childrenTypeStatusChange = new EventEmitter<Object>();


  constructor(
    private _configService: ConfigService,
  ) { }

  ngOnInit() {
    this._configService.init(this.obj.modulePath)
      .subscribe(()=>{
        this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
        this.backendUrl = this._configService.backendUrl()

        // status
        this.children0Array = Object.keys(this.obj.children0())
          .map( key => this.obj.children0()[key]);  //
        this.obj.childrenTypes().forEach((childrenType) => {
          this.childrenStatus[childrenType] = []
        });

        // datatable
        this.childrenDataTable = this.obj.childrenColumnsAndRows('display_list');

        this.medias = this.obj.children['media'] && this.obj.children['media'].map(e => e.properties)
      });
  }

  onSelectedChildren(childrenType, event) {
    this.childrenStatus[childrenType]=event;
    this.childrenTypeStatus = !this.childrenTypeStatus;
    this.childrenTypeStatusChange.emit("");
    setTimeout(() => {
      this.childrenTypeStatusChange.emit(childrenType);
    },100);
  }
  
}
