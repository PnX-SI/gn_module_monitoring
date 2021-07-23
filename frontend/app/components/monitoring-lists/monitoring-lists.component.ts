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

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() currentUser;

  activetab:string;

  frontendModuleMonitoringUrl;
  backendUrl: string;

  children0Array = [];

  childrenDataTable;
  tempChildrenRows;
  childrenColumns;

  queyParamsNewObject = {};

  // medias;

  @Input() objectsStatus: Object;
  @Output() objectsStatusChange: EventEmitter<Object> = new EventEmitter<Object>();

  constructor(
    private _configService: ConfigService,
  ) { }

  ngOnInit() {
    this._configService.init(this.obj.moduleCode)
      .subscribe(() => {
        this.initDataTable();
      });
  }

  initDataTable() {
    for (const key of Object.keys(this.obj.children)) {
      this.queyParamsNewObject[key] = {};
      this.queyParamsNewObject[key][this.obj.idFieldName()] = this.obj.id;
      this.queyParamsNewObject[key]['parents_path'] = this.obj.parentsPath.concat([this.obj.objectType]);
    }

    this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
    this.backendUrl = this._configService.backendUrl();

    this.children0Array = this.obj.children0Array();
    this.activetab = this.children0Array[0] && this.children0Array[0].objectType;
    // datatable
    this.childrenDataTable = this.obj.childrenColumnsAndRows('display_list');

    // this.medias = this.obj.children['media'] && this.obj.children['media'].map(e => e.properties);
  }

  onSelectedChildren(typeObject, event) {
    this.objectsStatus[typeObject] = event;
    let status_type = Utils.copy(this.objectsStatus)
    status_type["type"] = typeObject
    this.objectsStatusChange.emit(status_type);
  }

  changeActiveTab(typeObject) {
    this.activetab = typeObject;
    // Réinitialisation des données selectés
    this.objectsStatusChange.emit(this.reInitStatut());
  }

  reInitStatut() {
    let status_type = Utils.copy(this.objectsStatus)
    for (let typeObject in status_type) {
      if (Array.isArray(status_type[typeObject])) {
        for (let i in status_type[typeObject]) {
          try {
            status_type[typeObject][i]["selected"] = false;
          } catch (error) {
            console.error(error.message,  status_type[typeObject][i])
          }
        }
      }
    }
    return status_type
  }
  onbEditChanged(event) {
    this.bEditChange.emit(event);
  }

  displayNumber(chidrenType) {
    if(!this.objectsStatus[chidrenType]) {
      return '';
    }
    const visibles = this.objectsStatus[chidrenType].filter(s => s.visible)
    const nbSelected = visibles.length;
    const nb = this.obj.children[chidrenType].length;
    return nb == nbSelected
    ? `(${nb})`
    : `(${nbSelected}/${nb})`
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
