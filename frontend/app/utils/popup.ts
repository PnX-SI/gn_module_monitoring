import { Injectable } from '@angular/core';
import { ConfigService } from '../services/config.service';

@Injectable({
  providedIn: 'root',
})
export class Popup {
  constructor(private _configService: ConfigService) {}

  setPopup(
    moduleCode: string,
    objectType: string,
    feature,
    fieldId: string,
    fieldName: string,
    queryParams: {}
  ): string {
    const url = ['object', moduleCode, objectType, feature.properties[fieldId]].join('/');

    const fullurl = ['#', this._configService.frontendModuleMonitoringUrl(), url].join('/');
    const url_params = Object.keys(queryParams).length
      ? '?' +
        Object.keys(queryParams)
          .map((key) =>
            Array.isArray(queryParams[key])
              ? queryParams[key].map((val) => `${key}=${val}`).join('&')
              : `${key}=${queryParams[key]}`
          )
          .join('&')
      : '';

    const popup = `
    <div>
      <h4>  <a href=${fullurl}${url_params}>${feature.properties[fieldName]}</a></h4>
      ${feature.properties['description'] || ''}
    </div>
    `;
    return popup;
  }

  setSitePopup(moduleCode: string, feature, queryParams: {}) {
    return this.setPopup(
      moduleCode,
      'site',
      feature,
      'id_base_site',
      'base_site_name',
      queryParams
    );
  }

  setSiteGroupPopup(moduleCode: string, feature, queryParams: {}) {
    return this.setPopup(
      moduleCode,
      'sites_group',
      feature,
      'id_sites_group',
      'sites_group_name',
      queryParams
    );
  }
}
