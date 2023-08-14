import { Component, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs';

import { endPoints } from '../../enum/endpoints';
import { ISite, ISiteType } from '../../interfaces/geom';
import { IobjObs, ObjDataType, SiteSiteGroup } from '../../interfaces/objObs';
import { SitesGroupService, SitesService } from '../../services/api-geom.service';
import { FormService } from '../../services/form.service';
import { ObjectService } from '../../services/object.service';
import { JsonData } from '../../types/jsondata';
import { IPaginated } from '../../interfaces/page';
import { IBreadCrumb } from '../../interfaces/object';
import { breadCrumbElementBase } from '../breadcrumbs/breadcrumbs.component';

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
  id_sites_group: number | null;
  types_site: string[];
  config: JsonData;
  objToCreate: IobjObs<ObjDataType>;
  urlRelative: string;

  breadCrumbList: IBreadCrumb[] = [];
  breadCrumbElemnt: IBreadCrumb = { label: 'Groupe de site', description: '' };
  breadCrumbElementBase: IBreadCrumb = breadCrumbElementBase;

  constructor(
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _sitesGroupService: SitesGroupService,
    public siteService: SitesService,
    private route: ActivatedRoute,
    private _objService: ObjectService
  ) {}

  ngOnInit() {
    this.urlRelative = this.removeLastPart(this.route.snapshot['_routerState'].url);
    this.route.data.subscribe(({ data }) => {
      data ? (this.id_sites_group = data.id_sites_group) : (this.id_sites_group = null);

      this._formService.dataToCreate(
        {
          module: 'generic',
          objectType: 'site',
          id: null,
          id_sites_group: this.id_sites_group,
          id_relationship: ['id_sites_group', 'types_site'],
          endPoint: endPoints.sites,
          objSelected: data ? data.objectType : {},
        },
        this.urlRelative
      );
      this.form = this._formBuilder.group({});
      this.funcToFilt = this.partialfuncToFilt.bind(this);
      data ? this.updateBreadCrumb(data) : null;
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
    this.config = this.addTypeSiteListIds(config);
    this.createFormSpec();
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

  createFormSpec() {
    this._formService.createSpecificForm(this.config);
  }

  updateBreadCrumb(sitesGroup) {
    this.breadCrumbElemnt.description = sitesGroup.sites_group_name;
    this.breadCrumbElemnt.label = 'Groupe de site';
    this.breadCrumbElemnt['id'] = sitesGroup.id_sites_group;
    this.breadCrumbElemnt['objectType'] =
      this._sitesGroupService.objectObs.objectType || 'sites_group';
    this.breadCrumbElemnt['url'] = [
      this.breadCrumbElementBase.url,
      this.breadCrumbElemnt.id?.toString(),
    ].join('/');

    this.breadCrumbList = [this.breadCrumbElementBase, this.breadCrumbElemnt];
    this._objService.changeBreadCrumb(this.breadCrumbList, true);
  }
}
