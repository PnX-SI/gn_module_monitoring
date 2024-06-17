import { DataMonitoringObjectService } from './../../services/data-monitoring-object.service';
import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { ConfigService } from '../../services/config.service';

import { MonitoringObject } from '../../class/monitoring-object';

import { Utils } from '../../utils/utils';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { ListService } from '../../services/list.service';

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
  @Output() filtersChange: EventEmitter<Object> = new EventEmitter<Object>();

  @Input() selectedObject;
  @Output() selectedObjectChange: EventEmitter<string> = new EventEmitter<string>();

  nbVisibleRows: Record<string, number> = {};
  frontendModuleMonitoringUrl;
  backendUrl: string;

  children0Array = [];

  childrenDataTable;
  tempChildrenRows;
  childrenColumns;

  queyParamsNewObject = {};

  // medias;
  canCreateChild: { [key: string]: boolean } = {};
  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;
  constructor(
    private _configService: ConfigService,
    private _listService: ListService
  ) {}

  ngOnInit() {
    // Permet d'éviter une double initialisation du composant
    // this._configService.init(this.obj.moduleCode).subscribe(() => {
    //   this.initDataTable();
    // });
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
    const nb_row = event['nb_row'];
    this.nbVisibleRows[type] = nb_row;
  }

  changeActiveTab(typeObject, tab) {
    const activetab = this.children0Array[typeObject['index']];
    // Réinitialisation des données selectés
    this._listService.listType = activetab['objectType'];
    this._listService.tableFilters =
      this._listService.arrayTableFilters$.getValue()[activetab['objectType']];
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
      }
    }
  }
}
