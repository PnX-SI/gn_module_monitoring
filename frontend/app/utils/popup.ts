import { Injectable } from '@angular/core';
import { ConfigService } from '../services/config.service';

@Injectable({
  providedIn: 'root',
})
export class Popup {
  constructor(private _configService: ConfigService) {}

  setPopup(url: string, feature, fieldName: string): string {
    const fullurl = ['#', this._configService.frontendModuleMonitoringUrl(), url].join('/');
    const popup = `
    <div>
      <h4>  <a href=${fullurl}>${feature.properties[fieldName]}</a></h4>
      ${feature.properties['description'] || ''}
    </div>
    `;
    return popup;
  }

  setSitePopup(id: number, feature): string {
    const url = ['sites', id].join('/');
    return this.setPopup(url, feature, 'base_site_name');
  }
}
