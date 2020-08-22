import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { MonitoringObject } from '../../class/monitoring-object';
import { ConfigService } from '../../services/config.service';
import { MediaService } from '@geonature_common/service/media.service'

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

  constructor(
    private _configService: ConfigService,
    public ms: MediaService,
  ) {}

  ngOnInit() {
    this.backendUrl = this._configService.backendUrl();
  }

  onEditClick() {
    this.bEditChange.emit(true);
  }

}
