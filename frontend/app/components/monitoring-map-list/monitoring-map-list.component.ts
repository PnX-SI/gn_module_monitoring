import { Component } from '@angular/core';
import { SiteSiteGroup } from '../../interfaces/objObs';
import { MonitoringSitesComponent } from '../monitoring-sites/monitoring-sites.component';

@Component({
  selector: 'monitoring-map-list.component',
  templateUrl: './monitoring-map-list.component.html',
  styleUrls: ['./monitoring-map-list.component.css'],
})
export class MonitoringMapListComponent {
  displayMap: boolean = true;
  siteSiteGroup: SiteSiteGroup | null = null;
  constructor() {}

  onActivate(component) {
  }
}
