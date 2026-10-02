import { Component, OnInit, Input, AfterViewInit, Output, EventEmitter } from '@angular/core';
import { FormGroup, FormBuilder, Validators, FormControl, FormArray } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { forkJoin, Subscription } from 'rxjs';
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
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { PermissionService } from '../../services/permission.service';
import { ObjectService } from '../../services/object.service';
import { Popup } from '../../utils/popup';

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

  private hiddenTypesSite: number[] = [];
  private hiddenProperties: JsonData = {};

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
    _formUtils: MonitoringObjectService,
    translate: TranslateService,
    _configServiceG: ConfigServiceG,
    _permissionService: PermissionService,
    _objectService: ObjectService,
    _popup: Popup
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
      _formUtils,
      translate,
      _configServiceG,
      _permissionService,
      _objectService,
      _popup
    );
  }

  ngOnInit() {
    this.setAsideHiddenTypesSite();
    super.ngOnInit();
  }

  private setAsideHiddenTypesSite() {
    if (!this.object) {
      return;
    }

    // Récupération des propriétés supplémentaires
    // au module pour les mettre de coté
    this.hiddenProperties = {};
    this.object.additional_data_keys.forEach((key: string) => {
      this.hiddenProperties[key] = this.object[key];
    });

    // Récupération des types de site non définis dans
    // le module pour les mettre de coté
    let idsTypeSiteModule = this._configServiceG.config()?.['custom']?.['__MODULE.IDS_TYPE_SITE'];
    this.hiddenTypesSite = [];
    idsTypeSiteModule = idsTypeSiteModule.map((t) => t.id_nomenclature_type_site);
    const idsTypeSite: number[] = this.object.types_site || [];
    this.hiddenTypesSite = idsTypeSite.filter((id) => !idsTypeSiteModule.includes(id));
    this.object.types_site = idsTypeSite.filter((id) => idsTypeSiteModule.includes(id));
  }

  formatForApi(formValue: any): { [key: string]: any } {
    const data: { [key: string]: any } = super.formatForApi(formValue);

    // Suppression des propriétés appartenant aux types de site qui ont été supprimés
    // lors de la saisie utilisateur
    const deletedTypeSite: [number] = this.object.types_site.filter(
      (value: number) => !formValue.types_site.includes(value)
    );
    if (deletedTypeSite.length > 0) {
      const specificFields = (this.allSiteFormsDefinition as any[])
        .filter(
          (formDef) =>
            JSON.stringify((formDef.id_types_site || []).sort()) ===
            JSON.stringify(deletedTypeSite.sort())
        )
        .map((formDef) => formDef.attribut_name);
      specificFields.forEach((fieldName) => {
        if (fieldName in data) {
          delete data[fieldName];
        }
      });
    }

    // Rajout des types de site n'appartenant pas au module
    if (!this.hiddenTypesSite.length) {
      return data;
    }
    data['types_site'] = [...new Set([...(data['types_site'] || []), ...this.hiddenTypesSite])];

    // Rajout des propriétés n'appartenant pas au module
    const displayedFields = [
      ...(this.formsDefinition as any[]),
      ...this.typeSiteFormsDefinition.flatMap((typeSite) => typeSite.fields as any[]),
    ].map((formDef) => formDef.attribut_name);
    for (const [key, value] of Object.entries(this.hiddenProperties)) {
      if (!displayedFields.includes(key)) {
        data[key] = value;
      }
    }
    return data;
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

  /**
   * Déclenché quand un sous-formulaire "type de site" vient de (re)créer ses
   * contrôles. En édition, `monitoring-form-g` n'a pas pu pré-remplir ces
   * champs (ils n'existaient pas encore lors de son `formValues()` initial) :
   * on rejoue la résolution des valeurs depuis l'objet courant.
   */
  onTypeSiteFormGroupChange() {
    if (!this.object) {
      return;
    }

    this.formValues(this.object).subscribe((formValue) => {
      // Supprimer la clé 'types_site' sinon la valeur est réinitialisée à celle de l'objet
      delete formValue.types_site;
      this.form.patchValue(formValue);
    });
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
