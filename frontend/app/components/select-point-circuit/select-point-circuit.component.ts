import { Component, OnInit, Input, EventEmitter, Output, OnChanges } from '@angular/core';
import { FormControl } from '@angular/forms';

import { ConfigService } from "../../services/config.service";
import { DataMonitoringObjectService } from "../../services/data-monitoring-object.service";


@Component({
  selector: 'pnx-select-point-circuit',
  templateUrl: './select-point-circuit.component.html',
  styleUrls: ['./select-point-circuit.component.css']
})
export class SelectPointCircuitComponent implements OnInit {

  constructor(
    private _configService: ConfigService,
    private _data: DataMonitoringObjectService,
  ) { }

  @Input() parentFormControl: FormControl;
  @Input() idCircuit;
  points = [];

  ngOnInit() {

    this._configService.init().subscribe(() => {
      this._data.getCircuitPointsData(this.idCircuit).subscribe((points) => {
       this.points = points 
      });
    });
  }

}
