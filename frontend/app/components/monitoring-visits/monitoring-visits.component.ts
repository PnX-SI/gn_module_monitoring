import { Component, Input, OnInit, QueryList, ViewChild, ViewChildren } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable, forkJoin, iif, of } from 'rxjs';
import { map, mergeMap, take } from 'rxjs/operators';

import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { ISite, ISiteType } from '../../interfaces/geom';
import { IPage, IPaginated } from '../../interfaces/page';
import { IVisit } from '../../interfaces/visit';
import { SitesGroupService, SitesService, VisitsService } from '../../services/api-geom.service';
import { GeoJSONService } from '../../services/geojson.service';
import { ObjectService } from '../../services/object.service';
import { JsonData } from '../../types/jsondata';
import { IBreadCrumb, SelectObject } from '../../interfaces/object';
import { Module } from '../../interfaces/module';
import { ConfigService } from '../../services/config.service';
import { FormService } from "../../services/form.service";
import { breadCrumbElementBase } from '../breadcrumbs/breadcrumbs.component';
@Component({
  selector: 'monitoring-visits',
  templateUrl: './monitoring-visits.component.html',
  styleUrls: ['./monitoring-visits.component.css'],
})
export class MonitoringVisitsComponent extends MonitoringGeomComponent implements OnInit {
  site: ISite;
  @Input() visits: IVisit[];
  @Input() page: IPage;
  // colsname: typeof columnNameVisit = columnNameVisit;
  @Input() bEdit: boolean;
  form: FormGroup;
  colsname: {};
  objParent: any;
  modules: SelectObject[];

  isInitialValues: boolean;
  paramToFilt: string = 'label';
  funcToFilt: Function;
  funcInitValues: Function;
  titleBtn: string = 'Choix des types de sites';
  placeholderText: string = 'Sélectionnez les types de site';
  id_sites_group: number;
  types_site: string[];
  config: JsonData;
  siteGroupIdParent: number;
  breadCrumbParent: IBreadCrumb = { label: 'Groupe de site', description: '' };
  breadCrumbChild: IBreadCrumb = { label: 'Site', description: '' };
  breadCrumbElementBase: IBreadCrumb = breadCrumbElementBase;
  breadCrumbList: IBreadCrumb[] = [];

  constructor(
    private _sitesGroupService: SitesGroupService,
    private _visits_service: VisitsService,
    private _objService: ObjectService,
    public geojsonService: GeoJSONService,
    private router: Router,
    private _Activatedroute: ActivatedRoute,
    private _formBuilder: FormBuilder,
    private _formService: FormService,
    private _configService: ConfigService,
    private _siteService: SitesService
  ) {
    super();
    this.getAllItemsCallback = this.getVisits;
  }

  ngOnInit() {
    this.funcInitValues = this.initValueToSend.bind(this);
    this.funcToFilt = this.partialfuncToFilt.bind(this);
    this.form = this._formBuilder.group({});
    this._objService.changeObjectTypeParent(this._siteService.objectObs, true);
    this._objService.currentObjectTypeParent
      .pipe(take(1))
      .subscribe((objParent) => (this.objParent = objParent));

    this._objService.changeObjectType(this._visits_service.objectObs);

    this.siteGroupIdParent = parseInt(
      this._Activatedroute.pathFromRoot[this._Activatedroute.pathFromRoot.length - 2].snapshot
        .params['id']
    );
    this.initSiteVisit();
  }

  initSiteVisit() {
    this._Activatedroute.params
      .pipe(
        map((params) => params['id'] as number),
        mergeMap((id: number) =>
          forkJoin({
            site: this._siteService.getById(id),
            visits: this._visits_service.get(1, this.limit, {
              id_base_site: id,
            }),
          })
        ),
        mergeMap((data: { site: ISite; visits: IPaginated<IVisit> }) => {
          return this._objService.currentParentObjSelected.pipe(
            take(1),
            map((objSelectParent) => {
              return { site: data.site, visits: data.visits, parentObjSelected: objSelectParent };
            })
          );
        }),
        mergeMap((data) => {
          return iif(
            () => data.parentObjSelected == this.siteGroupIdParent,
            of(data),
            this._sitesGroupService.getById(this.siteGroupIdParent).pipe(
              map((objSelectParent) => {
                return { site: data.site, visits: data.visits, parentObjSelected: objSelectParent };
              })
            )
          );
        })
      )
      .subscribe((data) => {
        this._objService.changeSelectedObj(data.site, true);
        this.site = data.site;
        this.types_site = data.site['types_site'];
        this.setVisits(data.visits);
        this.baseFilters = { id_base_site: this.site.id_base_site };

        this.updateBreadCrumb(data.site, data.parentObjSelected);
      });
    this.isInitialValues = true;
  }

  getVisits(page: number, filters: JsonData) {
    this._visits_service
      .get(page, this.limit, filters)
      .subscribe((visits: IPaginated<IVisit>) => this.setVisits(visits));
  }

  setVisits(visits) {
    this.visits = visits.items;
    this.page = {
      page: visits.page - 1,
      count: visits.count,
      limit: visits.limit,
    };
    this.colsname = this._visits_service.objectObs.dataTable.colNameObj;
  }

  seeDetails($event) {
    this.router.navigate([
      `monitorings/object/${$event.module.module_code}/visit/${$event.id_base_visit}`,
    ]);
  }

  getModules() {
    this._siteService.getSiteModules(this.site.id_base_site).subscribe(
      (data: Module[]) =>
        (this.modules = data.map((item) => {
          return { id: item.module_code, label: item.module_label };
        }))
    );
  }

  addNewVisit($event: SelectObject) {
    const moduleCode = $event.id;
    //create_object/cheveches_sites_group/visit?id_base_site=47
    this._configService.init(moduleCode).subscribe(() => {
      const keys = Object.keys(this._configService.config()[moduleCode]);
      const parent_paths = ['sites_group', 'site'].filter((item) => keys.includes(item));
      this.router.navigate([`monitorings/create_object/${moduleCode}/visit`], {
        queryParams: { id_base_site: this.site.id_base_site, parents_path: parent_paths },
      });
    });
  }
  partialfuncToFilt(
    pageNumber: number,
    limit: number,
    valueToFilter: string
  ): Observable<IPaginated<ISiteType>> {
    return this._siteService.getTypeSites(pageNumber, limit, {
      label_fr: valueToFilter,
      sort_dir: 'desc',
    });
  }

  onSendConfig(config: JsonData): void {
    this.config = this.addTypeSiteListIds(config);
    this.updateForm();
    // this.monitoringFormComponentG.getConfigFromBtnSelect(this.config);
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

  initValueToSend() {
    this.initSiteVisit();
    return this.types_site;
  }

  updateForm() {
    this.site.specific = {};
    this.site.dataComplement = {};
    for (const key in this.config) {
      if (this.config[key].config != undefined) {
        if (Object.keys(this.config[key].config).length !== 0) {
          Object.assign(this.site.specific, this.config[key].config.specific);
        }
      }
    }
    for (const k in this.site.data) this.site[k] = this.site.data[k];
    this.site.types_site = this.config.types_site;
    Object.assign(this.site.dataComplement, this.config);

    this._formService.changeDataSub(this.site, this.objParent.objectType, this.objParent.endPoint);
  }

  updateBreadCrumb(site, parentSelected) {
    this.breadCrumbParent.description = parentSelected.sites_group_name;
    this.breadCrumbParent.label = 'Groupe de site';
    this.breadCrumbParent['id'] = parentSelected.id_sites_group;
    this.breadCrumbParent['objectType'] =
      this._sitesGroupService.objectObs.objectType || 'sites_group';
    this.breadCrumbParent['url'] = [
      this.breadCrumbElementBase.url,
      this.breadCrumbParent.id?.toString(),
    ].join('/');

    this.breadCrumbChild.description = site.base_site_name;
    this.breadCrumbChild.label = 'Site';
    this.breadCrumbChild['id'] = site.id_base_site;
    this.breadCrumbChild['objectType'] = this._siteService.objectObs.objectType || 'site';
    this.breadCrumbChild['url'] = [
      this.breadCrumbElementBase.url,
      this.breadCrumbParent.id?.toString(),
      this.breadCrumbChild.objectType,
      this.breadCrumbChild.id?.toString(),
    ].join('/');

    this.breadCrumbList = [this.breadCrumbElementBase, this.breadCrumbParent, this.breadCrumbChild];
    this._objService.changeBreadCrumb(this.breadCrumbList, true);
  }

  onObjChanged($event) {
    this.initSiteVisit();
  }
}
