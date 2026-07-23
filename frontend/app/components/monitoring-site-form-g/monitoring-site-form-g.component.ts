import { Component, OnInit, Input, AfterViewInit, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators, FormControl, FormArray } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { Location } from '@angular/common';

import { CommonService } from '@geonature_common/service/common.service';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';

import { MonitoringFormGComponent } from '../monitoring-form-g/monitoring-form-g.component';
import { FormService } from '../../services/form.service';
import { DataUtilsService } from '../../services/data-utils.service';
import { JsonData } from '../../types/jsondata';
import { GeoJSONService } from '../../services/geojson.service';
import { NavigationService } from '../../services/navigation.service';

@Component({
  selector: 'pnx-monitoring-site-form-g',
  templateUrl: './monitoring-site-form-g.component.html',
  styleUrls: ['./monitoring-site-form-g.component.css'],
})
export class MonitoringSiteFormGComponent extends MonitoringFormGComponent {
  private allSiteFormsDefinition: JsonData = [];
  public typeSiteFormsDefinition: { idType: number; name: string; fields: JsonData[] }[] = [];

  private typeSiteFieldsCache: { [idType: number]: JsonData[] } = {};

  private typesSiteValueChangesSub: Subscription;

  constructor(
    _commonService: CommonService,
    _formService: FormService,
    _dataUtilsService: DataUtilsService,
    _dynformService: DynamicFormService,
    _formBuilder: FormBuilder,
    _location: Location,
    _geojsonService: GeoJSONService,
    _navigationService: NavigationService,
    _route: ActivatedRoute,
    translate: TranslateService
  ) {
    super(
      _commonService,
      _formService,
      _dataUtilsService,
      _dynformService,
      _formBuilder,
      _location,
      _geojsonService,
      _navigationService,
      _route,
      translate
    );
  }

  initFormDefiniton(schema: JsonData, meta: JsonData) {
    this.allSiteFormsDefinition = super.initFormDefiniton(schema, meta);
    this.typeSiteFieldsCache = {};
    return (this.allSiteFormsDefinition as any[]).filter(
      (formDef) => !(formDef.id_types_site || []).length
    );
  }

  private getTypeSiteFields(idType: number): JsonData[] {
    if (!this.typeSiteFieldsCache[idType]) {
      this.typeSiteFieldsCache[idType] = (this.allSiteFormsDefinition as any[]).filter((formDef) =>
        (formDef.id_types_site || []).includes(idType)
      );
    }
    return this.typeSiteFieldsCache[idType];
  }

  onDynamicFormGroupChange() {
    super.onDynamicFormGroupChange();

    this.typesSiteValueChangesSub?.unsubscribe();
    const typesSiteControl = this.form.get('types_site');
    if (!typesSiteControl) {
      this.typeSiteFormsDefinition = [];
      return;
    }
    this.updateTypeSiteFormsDefinition(typesSiteControl.value || []);
    this.typesSiteValueChangesSub = typesSiteControl.valueChanges.subscribe(
      (idTypesSite: number[]) => {
        this.updateTypeSiteFormsDefinition(idTypesSite || []);
      }
    );
  }

  updateTypeSiteFormsDefinition(typesSiteids: number[]) {
    const typesSiteConfig = this.config['types_site'] || {};
    this.typeSiteFormsDefinition = typesSiteids
      .filter((idType) => typesSiteConfig[idType])
      .map((idType) => ({
        idType,
        name: typesSiteConfig[idType]['name'],
        fields: this.getTypeSiteFields(idType),
      }));
  }

  resetDynamicForm() {
    super.resetDynamicForm();
    this.typeSiteFormsDefinition = this.typeSiteFormsDefinition.map((typeSite) => ({
      ...typeSite,
      fields: typeSite.fields.map((formDef) => ({ ...formDef })),
    }));
  }

  ngOnDestroy() {
    this.typesSiteValueChangesSub?.unsubscribe();
    super.ngOnDestroy();
  }

  trackByTypeSiteId(index: number, typeSite: any) {
    return typeSite.idType;
  }
}
