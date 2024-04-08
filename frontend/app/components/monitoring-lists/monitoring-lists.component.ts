import { DataMonitoringObjectService } from './../../services/data-monitoring-object.service';
import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { ConfigService } from '../../services/config.service';

import { MonitoringObject } from '../../class/monitoring-object';

import { Utils } from '../../utils/utils';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';

@Component({
  selector: 'pnx-monitoring-lists',
  templateUrl: './monitoring-lists.component.html',
  styleUrls: ['./monitoring-lists.component.css'],
})
export class MonitoringListComponent implements OnInit {
  @Input() obj: MonitoringObject;

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() currentUser;
  @Input() filters;
  @Input() forceReload;
  @Output() filtersChange: EventEmitter<Object> = new EventEmitter<Object>();
  @Input() objectListType: string;
  @Output() objectListTypeChange: EventEmitter<string> = new EventEmitter<string>();

  @Input() selectedObject;
  @Output() selectedObjectChange: EventEmitter<string> = new EventEmitter<string>();

  @Output() onDeleteRow: EventEmitter<Object> = new EventEmitter<Object>();

  activetab: string;
  nbVisibleRows: Record<string, number> = {};
  frontendModuleMonitoringUrl;
  backendUrl: string;

  children0Array = [];

  childrenDataTable;
  tempChildrenRows;
  childrenColumns;

  queyParamsNewObject = {};

  // medias;
  @Output() objectsStatusChange: EventEmitter<Object> = new EventEmitter<Object>();

  canCreateChild: { [key: string]: boolean } = {};
  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;
  constructor(private _configService: ConfigService) {}

  ngOnInit() {
    this._configService.init(this.obj.moduleCode).subscribe(() => {
      this.initDataTable();
    });
  }

  initDataTable() {
    for (const key of Object.keys(this.obj.children)) {
      this.queyParamsNewObject[key] = {};
      this.queyParamsNewObject[key][this.obj.idFieldName()] = this.obj.id;
      this.queyParamsNewObject[key]['parents_path'] = this.obj.parentsPath.concat([
        this.obj.objectType,
      ]);
    }

    this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
    this.backendUrl = this._configService.backendUrl();

    this.children0Array = this.obj.children0Array();
    this.activetab = this.children0Array[0] && this.children0Array[0].objectType;

    this.objectListType = this.children0Array[0] && this.children0Array[0].objectType;

    // datatable
    this.childrenDataTable = this.obj.childrenColumnsAndRows('display_list');

    // Initialisation nombre d'élément affiché dans la liste
    Object.keys(this.childrenDataTable).forEach((chidrenType) => {
      this.nbVisibleRows[chidrenType] = this.childrenDataTable[chidrenType].rows.length;
    });
    this.initPermission();
    // this.medias = this.obj.children['media'] && this.obj.children['media'].map(e => e.properties);
  }

  initPermission() {
    for (const child of this.children0Array) {
      const childType = child['objectType'];
      this.canCreateChild[childType] = this.currentUser?.moduleCruved[childType].C > 0;
    }
  }

  onSelectedChildren(typeObject, event) {
    this.selectedObject = event;
    this.selectedObjectChange.emit(event);
  }

  onFilterChange(type, event) {
    const filters = event['filters'];
    const nb_row = event['nb_row'];
    if (event) {
      this.filters = filters;
      this.filtersChange.emit(Utils.copy(this.filters));
      this.objectListTypeChange.emit(Utils.copy(this.objectListType));
    }
    this.nbVisibleRows[type] = nb_row;
  }

  onDeleteRowChange(event) {
    this.onDeleteRow.emit(event);
  }

  changeActiveTab(typeObject, tab) {
    this.activetab = this.children0Array[typeObject['index']];
    // Réinitialisation des données selectés
    this.objectListType = this.children0Array[typeObject['index']]['objectType'];
    this.objectListTypeChange.emit(this.objectListType);
  }

  onbEditChanged(event) {
    this.bEditChange.emit(event);
  }

  displayNumber(chidrenType) {
    if (!this.childrenDataTable[chidrenType]) {
      return '';
    }

    const nbSelected = this.nbVisibleRows[chidrenType];
    const nb = this.childrenDataTable[chidrenType]['rows'].length;

    return nb == nbSelected ? `(${nb})` : `(${nbSelected}/${nb})`;
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
        case 'forceReload':
          this.initDataTable();
          break;
      }
    }
  }
}
