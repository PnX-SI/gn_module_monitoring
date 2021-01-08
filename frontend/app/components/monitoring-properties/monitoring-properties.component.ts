import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { MonitoringObject } from '../../class/monitoring-object';
import { ConfigService } from '../../services/config.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { CommonService } from '@geonature_common/service/common.service';
import { MediaService } from '@geonature_common/service/media.service';


@Component({
  selector: 'pnx-monitoring-properties',
  templateUrl: './monitoring-properties.component.html',
  styleUrls: ['./monitoring-properties.component.css']
})
export class MonitoringPropertiesComponent implements OnInit {

  @Input() obj: MonitoringObject;
  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() currentUser;

  backendUrl: string;
  bUpdateSyntheseSpinner = false;

  constructor(
    private _configService: ConfigService,
    public ms: MediaService,
    private _dataService: DataMonitoringObjectService,
    private _commonService: CommonService,
  ) {}

  ngOnInit() {
    this.backendUrl = this._configService.backendUrl();
  }

  onEditClick() {
    this.bEditChange.emit(true);
  }

  updateSynthese() {
    this.bUpdateSyntheseSpinner = true;
    this._dataService.updateSynthese(this.obj.moduleCode).subscribe(
      () => {
        this.bUpdateSyntheseSpinner = false;
        this._commonService.regularToaster('success', `La syntèse à été mise à jour pour le module ${this.obj.moduleCode}`);
      },
      (err) => {
        this.bUpdateSyntheseSpinner = false;
        this._commonService.regularToaster('error', `Erreur lors de la mise à jour de la syntèse pour le module ${this.obj.moduleCode} - ${err.error.message}`);
      }
    );
  }

}
