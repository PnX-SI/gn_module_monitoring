import { Component, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs';

import { endPoints } from '../../enum/endpoints';
import { ISite, ISiteType } from '../../interfaces/geom';
import { IobjObs, ObjDataType } from '../../interfaces/objObs';
import { SitesService } from '../../services/api-geom.service';
import { FormService } from '../../services/form.service';
import { ObjectService } from '../../services/object.service';
import { JsonData } from '../../types/jsondata';
import { MonitoringFormComponentG } from '../monitoring-form-g/monitoring-form.component-g';
import { IPaginated } from '../../interfaces/page';

@Component({
  selector: 'monitoring-sites-create',
  templateUrl: './monitoring-sites-create.component.html',
  styleUrls: ['./monitoring-sites-create.component.css'],
})
export class MonitoringSitesCreateComponent implements OnInit {
  site: ISite;
  form: FormGroup;
  paramToFilt: string = 'label';
  funcToFilt: Function;
  titleBtn: string = 'Choix des types de sites';
  placeholderText: string = 'Sélectionnez les types de site';
  id_sites_group: number;
  types_site: string[];
  @ViewChild('subscritionObjConfig')
  monitoringFormComponentG: MonitoringFormComponentG;
  objToCreate: IobjObs<ObjDataType>;
  urlRelative: string;
  constructor(
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    public siteService: SitesService,
    private route: ActivatedRoute,
    private _objService: ObjectService
  ) {}

  ngOnInit() {
    this.urlRelative = this.removeLastPart(this.route.snapshot['_routerState'].url);
    this._objService.currentObjSelected.subscribe((objParent) => {
      this.id_sites_group = objParent.id_sites_group;
      this._formService.dataToCreate(
        {
          module: 'generic',
          objectType: 'site',
          id: null,
          id_sites_group: this.id_sites_group,
          id_relationship: ['id_sites_group', 'types_site'],
          endPoint: endPoints.sites,
          objSelected: objParent.objectType,
        },
        this.urlRelative
      );
      this.form = this._formBuilder.group({});
      this.funcToFilt = this.partialfuncToFilt.bind(this);
    });
  }

  removeLastPart(url: string): string {
    return url.slice(0, url.lastIndexOf('/'));
  }


  partialfuncToFilt(
    pageNumber: number,
    limit: number,
    valueToFilter: string
  ): Observable<IPaginated<ISiteType>> {
    return this.siteService.getTypeSites(pageNumber, limit, {
      label_fr: valueToFilter,
      sort_dir: 'desc',
    });
  }

  onSendConfig(config: JsonData): void {
    config = this.addTypeSiteListIds(config);
    this.monitoringFormComponentG.getConfigFromBtnSelect(config);
  }

  addTypeSiteListIds(config: JsonData): JsonData {
    if (config && config.length != 0) {
      config.types_site = [];
      for (const key in config) {
        if ('id_nomenclature_type_site' in config[key]) {
          config.types_site.push(config[key]['id_nomenclature_type_site']);
        }
      }
    }
    return config;
  }
}
