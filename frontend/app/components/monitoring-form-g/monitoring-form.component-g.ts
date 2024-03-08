import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import {
  tap,
  mergeMap,
  map,
  take,
  switchMap,
  concatMap,
  takeUntil,
  distinctUntilChanged,
} from 'rxjs/operators';
import { ActivatedRoute } from '@angular/router';
import { Router } from '@angular/router';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';
import { CommonService } from '@geonature_common/service/common.service';

import { IDataForm } from '../../interfaces/form';
import { ApiGeomService } from '../../services/api-geom.service';
import { ConfigJsonService } from '../../services/config-json.service';
import { FormService } from '../../services/form.service';
import { IExtraForm } from '../../interfaces/object';
import { JsonData } from '../../types/jsondata';
import { Observable, ReplaySubject, Subject, of } from 'rxjs';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { GeoJSONService } from '../../services/geojson.service';

@Component({
  selector: 'pnx-monitoring-form-g',
  templateUrl: './monitoring-form.component-g.html',
  styleUrls: ['./monitoring-form.component-g.css'],
})
export class MonitoringFormComponentG implements OnInit {
  @Input() currentUser;

  @Input() objForm: {
    static: FormGroup;
    dynamic?: FormGroup;
  };
  // @Input() objForm: FormGroup;
  objFormStatic: FormGroup;
  objFormDynamic: FormGroup;

  // @Input() obj: any;
  @Output() objChanged = new EventEmitter<Object>();

  @Input() objectsStatus;
  @Output() objectsStatusChange = new EventEmitter<Object>();

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() sites: {};
  @Input() apiService: ApiGeomService;
  @Input() isExtraForm: boolean = false;

  extraFormCtrl: IExtraForm;
  geomCtrl: { frmCtrl: FormControl; frmName: string };
  dataForm: IDataForm;
  searchSite = '';

  isExtraControlChange: boolean;
  isUndefinedChange: boolean;
  obj: JsonData;
  objFormsDefinition: {
    static: JsonData[];
    dynamic?: JsonData[];
  };

  objFormGroups: FormGroup;
  prop: JsonData;
  specificForm$: Observable<any>;
  createSpecificForm$: Observable<JsonData>;
  meta: {};
  private destroyed$: ReplaySubject<boolean> = new ReplaySubject(1);

  public bSaveSpinner = false;
  public bSaveAndAddChildrenSpinner = false;
  public bDeleteSpinner = false;
  public bDeleteModal = false;
  public bChainInput = false;
  public bAddChildren = false;
  public chainShow = [];
  public queryParams = {};

  canDelete: boolean = false;
  canUpdate: boolean = false;
  canCreateOrUpdate: boolean = false;
  geomCalculated: boolean = false;

  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;
  constructor(
    private _formBuilder: FormBuilder,
    private _route: ActivatedRoute,
    private _configService: ConfigJsonService,
    private _commonService: CommonService,
    private _dynformService: DynamicFormService,
    private _formService: FormService,
    private _router: Router,
    private _geojsonService: GeoJSONService
  ) { }

  ngOnInit() {
    if (!this.objFormStatic) {
      this.objFormStatic = this._formBuilder.group({});
    }
    if (!this.objFormDynamic && this.isExtraForm) {
      this.objFormDynamic = this._formBuilder.group({});
    }
    this.isExtraForm
      ? (this.objForm = { static: this.objFormStatic, dynamic: this.objFormDynamic })
      : (this.objForm = { static: this.objFormStatic });
    this.isExtraForm
      ? (this.objFormsDefinition = { static: [{}], dynamic: [{}] })
      : (this.objFormsDefinition = { static: [{}] });

    this.specificForm$ = this._formService.currentDataSpec.pipe(
      mergeMap((newObj) => {
        return this.apiService.getConfig().pipe(
          map((prop) => {
            this.prop = prop;
            return { newObj, prop: prop };
          })
        );
      })
    );

    this.createSpecificForm$ = this._formService.currentDataSpecToCreate.pipe(
      mergeMap((specConfig) => {
        return this.apiService.getConfig().pipe(
          map((prop) => {
            this.prop = prop;
            return { specConfig: specConfig, prop: prop };
          })
        );
      })
    );
    this._formService.currentData
      .pipe(
        distinctUntilChanged((prev, curr) => prev['pk'] === curr['pk']),
        takeUntil(this.destroyed$),
        tap((data) => {
          this.obj = data;
          this.obj.id = this.obj[this.obj.pk];
          this.initPermission();
          // this.bEdit ? this._geojsonService.setCurrentmapData(this.obj.geometry):null;
          // this.bEdit &&  this._geojsonService.currentLayer == null ? (this._geojsonService.removeAllFeatureGroup(),this._geojsonService.setCurrentmapData(this.obj.geometry)) : null;
        }),
        concatMap((data: any) => this._configService.init(data.moduleCode)),
        concatMap((data) => {
          return this.apiService.getConfig().pipe(
            map((prop) => {
              this.prop = prop;
              return { prop: prop };
            })
          );
        }),
        switchMap(({ prop }) => {
          if (this.isExtraForm) {
            return this._formService.currentExtraFormCtrl.pipe(
              map((frmCtrl) => {
                return { prop: prop, frmCtrl: frmCtrl };
              })
            );
          } else {
            return of({ prop: prop });
          }
        })
      )
      .subscribe((data) => {
        this.initObj(data.prop);
        this.obj.config = this._configService.configModuleObject(
          this.obj.moduleCode,
          this.obj.objectType
        );
        const schema = this._configService.schema(this.obj.moduleCode, this.obj.objectType);
        this.obj[this.obj.moduleCode] = schema;
        this.obj.specific == undefined ? (this.obj.specific = {}) : null;
        this.obj.bIsInitialized = true;

        this.queryParams = this._route.snapshot.queryParams || {};
        this.bChainInput = this._configService.frontendParams().bChainInput;
        // meta pour les parametres dynamiques
        // ici pour avoir acces aux nomenclatures
        this.meta = {
          // nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
          // dataset: this._dataUtilsService.getDataUtil('dataset'),
          id_role: this.currentUser.id_role,
          bChainInput: this.bChainInput,
          parents: this.obj.parents,
        };

        Object.keys(this.objFormsDefinition).forEach((key) => {
          let configType: string;
          key == 'static' ? (configType = 'generic') : (configType = 'specific');

          this.obj.config
            ? (this.objFormsDefinition[key] = this._dynformService
              .formDefinitionsdictToArray(this.obj[configType], this.meta)
              .filter((formDef) => formDef.type_widget)
              .sort((a, b) => {
                // medias à la fin
                return a.attribut_name === 'medias' ? +1 : b.attribut_name === 'medias' ? -1 : 0;
              }))
            : null;
        });

        // display_form pour customiser l'ordre dans le formulaire
        // les éléments de display form sont placé en haut dans l'ordre du tableau
        // tous les éléments non cachés restent affichés

        let displayProperties = [
          ...(this._configService.configModuleObjectParam(
            this.obj.moduleCode,
            this.obj.objectType,
            'display_properties'
          ) || []),
        ];
        if (displayProperties && displayProperties.length) {
          displayProperties.reverse();
          Object.keys(this.objFormsDefinition).forEach((key) => {
            this.objFormsDefinition[key].sort((a, b) => {
              let indexA = displayProperties.findIndex((e) => e == a.attribut_name);
              let indexB = displayProperties.findIndex((e) => e == b.attribut_name);
              return indexB - indexA;
            });
          });
        }
        this.objForm.static.addControl('patch_update', this._formBuilder.control(0));

        this.isExtraForm ? this.addExtraFormCtrl(data['frmCtrl']) : null;
        // set geometry
        if (this.obj.config && this.obj.config['geometry_type']) {
          const validatorRequired =
            this.obj.objectType == 'sites_group'
              ? this._formBuilder.control('')
              : this._formBuilder.control('', Validators.required);
          let frmCtrlGeom = {
            frmCtrl: validatorRequired,
            frmName: 'geometry',
          };
          this.addGeomFormCtrl(frmCtrlGeom);
        }
        this.initForm();
        this.isExtraForm && this.bEdit ? this.updateSpecificForm() : null;
        this.isExtraForm && !this.bEdit ? this.createSpecificForm() : null;
      });
    this.geomCalculated = this.obj.hasOwnProperty('is_geom_from_child')
      ? this.obj.is_geom_from_child
      : false;
    this.geomCalculated || this.obj.id == undefined ? (this.obj.geometry = null) : null;
    this.bEdit
      ? (this._geojsonService.removeAllFeatureGroup(),
        this._geojsonService.setCurrentmapData(this.obj.geometry, this.geomCalculated))
      : null;
  }

  /** pour réutiliser des paramètres déjà saisis */
  keepDefinitions() {
    return Object.keys(this.objFormsDefinition).forEach((key) => {
      this.objFormsDefinition[key].filter((def) =>
        this._configService
          .configModuleObjectParam(this.obj.moduleCode, this.obj.objectType, 'keep')
          .includes(def.attribut_name)
      );
    });
  }

  setQueryParams() {
    // par le biais des parametre query de route on donne l'id du ou des parents
    // permet d'avoir un 'tree' ou un objet est sur plusieurs branches
    // on attend des ids d'où test avec parseInt
    for (const key of Object.keys(this.queryParams)) {
      const strToInt = parseInt(this.queryParams[key]);
      if (!Number.isNaN(strToInt)) {
        this.obj.properties[key] = strToInt;
      }
    }
  }

  /** initialise le formulaire quand le formulaire est prêt ou l'object est prêt */

  initForm() {
    if (!(this.objForm.static && this.obj.bIsInitialized && this.obj.config)) {
      return;
    }

    this.setQueryParams();

    this._formService.formValues(this.obj).subscribe((formValue) => {
      const allKeysForm = Object.keys(formValue);
      const allKeysStatic = Object.keys(this.obj.config.generic);
      if (this.obj.config['geometry_type'] && allKeysForm.includes('geometry')) {
        allKeysStatic.push('geometry');
      }
      // const allKeysSpecific = Object.keys(this.obj.specific);
      let formValueStatic = {};
      for (let key of allKeysForm) {
        if (allKeysStatic.includes(key)) {
          formValueStatic[key] = formValue[key];
        }
      }
      this.objForm.static.patchValue(formValueStatic);
      this._formService.changeFormMapObj({
        frmGp: this.objForm.static,
        bEdit: true,
        obj: this.obj,
      });
      this.setDefaultFormValue();
    });
  }

  initValueFormDynamic() {
    if (!(this.objForm.dynamic && this.obj.bIsInitialized && this.obj.config)) {
      return;
    }

    this.setQueryParams();
    this._formService.formValues(this.obj).subscribe((formValue) => {
      const allKeysForm = Object.keys(formValue);
      const allKeysSpecific = Object.keys(this.obj.specific);
      let formValueSpecific = {};
      for (let key of allKeysForm) {
        if (allKeysSpecific.includes(key) || key == 'types_site') {
          formValueSpecific[key] = formValue[key];
        }
      }
      this.objForm.dynamic.patchValue(formValueSpecific);
      this.setDefaultFormValue();
      // this.dataForm = propertiesValues;
    });
  }

  keepNames() {
    return (
      this._configService.configModuleObjectParam(
        this.obj.moduleCode,
        this.obj.objectType,
        'keep'
      ) || []
    );
  }

  idFieldName() {
    return this._configService.configModuleObjectParam(
      this.obj.moduleCode,
      this.obj.objectType,
      'id_field_Name'
    );
  }

  resetObjForm() {
    //NEW- setResolvedProperties

    // quand on enchaine les relevés
    // const chainShow = this.obj.configParam('chain_show');

    //TODO: Ici chain_show est présent que dans le fichier de config visit.json
    // --> voir à quoi correspond ce chainShow où on utilise les propriétés (id_base_site, num_passage etc)
    const chainShow = this._configService.configModuleObjectParam(
      this.obj.moduleCode,
      this.obj.objectType,
      'chain_show'
    );
    if (chainShow) {
      this.chainShow.push(chainShow.map((key) => this.obj.resolvedProperties[key]));
      this.chainShow.push(this.obj.resolvedProperties);
    }

    // les valeur que l'on garde d'une saisie à l'autre
    const keep = {};
    for (const key of this.keepNames()) {
      keep[key] = this.obj.properties[key];
    }

    this.obj = {
      bIsInitialized: false,
      moduleCode: this.obj.moduleCode,
      objectType: this.obj.objectType,
      endPoint: this.obj.endPoint,
      properties: {},
      generic: this.obj.generic,
    };
    this.obj.config = this._configService.configModuleObject(
      this.obj.moduleCode,
      this.obj.objectType
    );
    this.obj.properties[this.idFieldName()] = null;

    // pq get ?????
    // this.obj.get(0).subscribe(() => {
    this.obj.bIsInitialized = true;
    for (const key of this.keepNames()) {
      this.obj.properties[key] = keep[key];
    }

    this.objChanged.emit(this.obj);
    this.objForm.static.patchValue({ geometry: null });
    this.objForm.dynamic?.patchValue({});
    this.initForm();
    this.isExtraForm ? this.initValueFormDynamic() : null;
    // };
  }

  /** Pour donner des valeurs par defaut si la valeur n'est pas définie
   * id_digitiser => current_user.id_role
   * observers => [current_user.id_role]
   * date => today
   */
  setDefaultFormValue() {
    const value = this.objForm.static.value;
    const date = new Date();
    const defaultValue = {
      id_digitiser: value['id_digitiser'] || this.currentUser.id_role,
      observers: value['observers'] || [this.currentUser.id_role],
      first_use_date: value['first_use_date'] || {
        year: date.getUTCFullYear(),
        month: date.getUTCMonth() + 1,
        day: date.getUTCDate(),
      },
    };
    this.objForm.static.patchValue(defaultValue);
  }

  /**
   * TODO faire des fonctions dans monitoring objet (ou moniotring objet service pour naviguer
   */

  /**
   * Valider et renseigner les enfants
   */
  navigateToAddChildren() {
    this.bEditChange.emit(false);
    this.obj.navigateToAddChildren();
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToDetail(id, objectType, queryParams) {
    // patch bug navigation
    // this._router.navigate(
    //   ['monitorings', objectType, id].filter((s) => !!s),
    //   {
    //     queryParams,
    //   }
    // );
    // TODO: this commented code works only if ".." is not based url (example working : sites_group/:id/site/:id , not working if create site_group)
    // this._router.navigate(['..',objectType,id], {relativeTo: this._route});
    const urlSegment =
      this.obj.urlRelative == '/monitorings'
        ? [this.apiService.objectObs.routeBase, id]
        : [objectType, id].filter((s) => !!s);
    const urlPathDetail = [this.obj.urlRelative].concat(urlSegment).join('/');
    this.objChanged.emit(this.obj);
    const urlRelative = this.obj.urlRelative ? true : false;
    if (urlRelative) {
      this._router.navigateByUrl(urlPathDetail);
    } else {
      const urlTree = this._router.parseUrl(this._router.url);
      const urlWithoutParams = urlTree.root.children['primary'].segments
        .map((it) => it.path)
        .join('/');
      this._router.navigate([urlWithoutParams]);
    }
    this.bEditChange.emit(false);
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToParent() {
    // FIXME:: voir erreur de redirection (comparaison avec branche où ça fonctionnait ?)
    this.bEditChange.emit(false); // patch bug navigation
    if (!this.bEdit) {
      this._router.navigate(['..'], { relativeTo: this._route });
    }
  }

  navigateToParentAfterDelete() {
    this.bEditChange.emit(false); // patch bug navigation
    if (this.obj.objectType == 'site' && this._router.url.includes('sites_group')) {
      this._router.navigate(['monitorings', 'sites_group', this._route.parent.snapshot.params.id]);
    } else {
      this._router.navigate(['..'], { relativeTo: this._route });
    }
  }

  msgToaster(action) {
    // return `${action} ${this.obj.labelDu()} ${this.obj.description()} effectuée`.trim();
    return `${action}  effectuée`.trim();
  }

  /** TODO améliorer site etc.. */
  onSubmit(isAddChildrend = false) {
    isAddChildrend
      ? (this.bSaveAndAddChildrenSpinner = this.bAddChildren = true)
      : (this.bSaveSpinner = true);
    const { patch_update, ...sendValue } = this.dataForm;
    const objToUpdateOrCreate = this._formService.postData(sendValue, this.obj);
    const action = this.obj.id
      ? this.apiService.patch(this.obj.id, objToUpdateOrCreate)
      : this.apiService.create(objToUpdateOrCreate);
    const actionLabel = this.obj.id ? 'Modification' : 'Création';
    action.subscribe((objData) => {
      this._commonService.regularToaster('success', this.msgToaster(actionLabel));
      this.bSaveSpinner = this.bSaveAndAddChildrenSpinner = false;

      Object.entries(objData['properties']).forEach(([key, value]) => {
        this.obj['properties'][key] = value;
      });

      if (objData.hasOwnProperty('id')) {
        this.obj.id = objData['id'];
      }
      this.objChanged.emit(this.obj);

      /** si c'est un module : reset de la config */
      if (this.obj.objectType === 'module') {
        this._configService.loadConfig(this.obj.moduleCode).subscribe();
      }

      if (this.bChainInput) {
        this.resetObjForm();
      } else if (this.bAddChildren) {
        this.navigateToAddChildren();
      } else {
        if (
          this._configService.configModuleObjectParam(
            this.obj.moduleCode,
            this.obj.objectType,
            'redirect_to_parent'
          )
        ) {
          this.navigateToParent();
        } else {
          this.navigateToDetail(this.obj.id, this.obj.objectType, this.queryParams);
        }
      }
    });
  }

  onCancelEdit() {
    if (this.bEdit) {
      const urlTree = this._router.parseUrl(this._router.url);
      const urlWithoutParams = urlTree.root.children['primary'].segments
        .map((it) => it.path)
        .join('/');
      this._router.navigate([urlWithoutParams]);

      this._geojsonService.removeAllFeatureGroup();
      this.obj.geometry == null
        ? this._geojsonService.setMapDataWithFeatureGroup([this._geojsonService.sitesFeatureGroup])
        : this._geojsonService.setMapBeforeEdit(this.obj.geometry);
      this.bEditChange.emit(false);
    } else {
      this.navigateToParent();
    }
  }

  onDelete() {
    this.bDeleteSpinner = true;
    // : this.obj.post(this.objForm.value);
    this.apiService.delete(this.obj.id).subscribe((del) => {
      this.bDeleteSpinner = this.bDeleteModal = false;
      this.objChanged.emit('deleted');
      setTimeout(() => {
        this._commonService.regularToaster('info', this.msgToaster('Suppression'));
        this.navigateToParentAfterDelete();
      }, 100);
    });
  }

  onObjFormValueChange(event) {
    // let {id_module,medias, ...rest} = this.objForm.value;
    // this.dataForm = rest
    this.dataForm = { ...this.objForm.static.value, ...this.objForm.dynamic?.value };
    const change = this._configService.change(this.obj.moduleCode, this.obj.objectType);
    // if('geometry' in this.objForm.controls){
    //   this._formService.changeFormMapObj({frmGp:this.objForm,bEdit:true, obj: this.obj})
    // }

    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objForm.static, meta: this.meta });
    }, 100);
  }

  onObjFormDynamicValueChange(event) {
    // let {id_module,medias, ...rest} = this.objForm.value;
    // this.dataForm = rest
    this.dataForm = { ...this.objForm.static.value, ...this.objForm.dynamic.value };
    const change = this._configService.change(this.obj.moduleCode, this.obj.objectType);
    // if('geometry' in this.objForm.controls){
    //   this._formService.changeFormMapObj({frmGp:this.objForm,bEdit:true, obj: this.obj})
    // }
    if (this.extraFormCtrl && !this.extraFormCtrl.frmCtrl.valid) {
      this.extraFormCtrl.frmCtrl.markAllAsTouched();
    }
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objForm.static, meta: this.meta });
    }, 100);
  }

  procesPatchUpdateForm() {
    Object.keys(this.objForm).forEach((form) =>
      this.objForm[form].patchValue({
        patch_update: this.objForm[form].value.patch_update + 1,
      })
    );
  }

  /** bChainInput gardé dans config service */
  bChainInputChanged() {
    for (const formDef of this.objFormsDefinition.static) {
      formDef.meta.bChainInput = this.bChainInput;
    }
    this._configService.setFrontendParams('bChainInput', this.bChainInput);
    // patch pour recalculers
    this.procesPatchUpdateForm();
  }

  addExtraFormCtrl(frmCtrl: IExtraForm) {
    if (frmCtrl.frmName in this.objFormDynamic.controls) {
    } else {
      this.objForm.dynamic.addControl(frmCtrl.frmName, frmCtrl.frmCtrl);
    }

    this.extraFormCtrl = frmCtrl;
  }

  addGeomFormCtrl(frmCtrl: { frmCtrl: FormControl; frmName: string }) {
    if (frmCtrl.frmName in this.objForm.static.controls) {
    } else {
      this.objForm.static.addControl(frmCtrl.frmName, frmCtrl.frmCtrl);
    }
    this.geomCtrl = frmCtrl;
  }

  getConfigFromBtnSelect(configSpec) {
    // TODO: Ajout de tous les id_parents ["id_sites_groups" etc ] dans l'objet obj.dataComplement
    // Check if specific and dataComplement already exist
    this.obj.specific = {};
    this.obj.dataComplement = {};

    Object.entries(configSpec).forEach(([key, value]) => {
      if (this.obj.dataComplement[key] && key != 'types_site') {
        return;
      }
      if (configSpec[key].config != undefined) {
        if (Object.keys(configSpec[key].config).length !== 0) {
          Object.assign(this.obj.specific, configSpec[key].config.specific);
          if ('keep' in configSpec[key].config) {
            this.obj.config.keep ? null : (this.obj.config.keep = []);
            !this.obj.config.keep.includes(configSpec[key].config.keep)
              ? this.obj.config.keep.push(...configSpec[key].config.keep)
              : null;
          }
        }
        this.obj.dataComplement[key] = value;
      } else {
        this.obj.dataComplement[key] ? null : (this.obj.dataComplement[key] = []);
        this.obj.dataComplement[key] = configSpec[key];
      }
    });
  }

  initObj(prop) {
    this.obj['properties'] = prop;
    Object.entries(this.obj).forEach(([key, value]) => {
      if (key != 'properties' && key in this.obj['properties']) {
        this.obj['properties'][key] = value;
      }
    });
    this.obj.resolvedProperties = this._configService.setResolvedProperties(this.obj);
  }

  updateExtraFormOnly() {
    if (!(this.objForm.dynamic && this.obj.bIsInitialized)) {
      return;
    }
    // pour donner la valeur de l'objet au formulaire
    this._formService.formValues(this.obj).subscribe((formValue) => {
      const allKeysForm = Object.keys(formValue);
      const allKeysGeneric = Object.keys(this.obj.config.generic);
      const allKeysSpecific = Object.keys(this.obj.specific);
      let formValueSpecific = {};
      for (let key of allKeysForm) {
        if (allKeysSpecific.includes(key)) {
          formValueSpecific[key] = formValue[key];
        }
      }
      this.objForm.dynamic.patchValue(formValueSpecific);
      // this.setDefaultFormValue();
      // this.dataForm = propertiesValues;
      // reset geom ?
    });
  }

  createSpecificForm() {
    this.createSpecificForm$.subscribe(({ specConfig, prop }) => {
      this.obj.bIsInitialized = true;
      this.obj.id = this.obj[this.obj.pk];
      this.getConfigFromBtnSelect(specConfig);
      this.initObj(prop);
      this.initElementFormDynamic();
      this.initValueFormDynamic();
    });
  }
  updateSpecificForm() {
    this.specificForm$.subscribe(({ newObj, prop }) => {
      this.obj.bIsInitialized = true;
      this.obj.id = this.obj[this.obj.pk];
      this.obj.dataComplement = newObj.newObj.dataComplement;
      this.obj.specific = newObj.newObj.specific;
      Object.assign(this.obj, newObj.propSpec);
      this.initObj(prop);
      this.initElementFormDynamic();
      this.initValueFormDynamic();
    });
  }

  initElementFormDynamic() {
    const schema = this._configService.schema(this.obj.moduleCode, this.obj.objectType);
    if (Object.keys(this.obj.specific).length !== 0) {
      Object.assign(schema, this.obj.specific);
    }

    this.obj[this.obj.moduleCode] = schema;
    this.objFormsDefinition.dynamic = this._dynformService
      .formDefinitionsdictToArray(this.obj.specific, this.meta)
      .filter((formDef) => formDef.type_widget)
      .sort((a, b) => {
        // medias à la fin
        return a.attribut_name === 'medias' ? +1 : b.attribut_name === 'medias' ? -1 : 0;
      });
  }

  initPermission() {
    !this.bEdit
      ? (this.canCreateOrUpdate = true)
      : ((this.canDelete = this.obj.cruved['D']),
        (this.canCreateOrUpdate = this.canUpdate = this.obj.cruved['U']));
  }

  notAllowedMessage() {
    this._commonService.translateToaster(
      'warning',
      "Vous n'avez pas les permissions nécessaires pour éditer l'objet"
    );
  }

  ngOnDestroy() {
    this._formService.changeFormMapObj({
      frmGp: this._formBuilder.group({}),
      bEdit: false,
      obj: {},
    });
    this.obj = {};
    this._formService.createSpecificForm({});
    this.destroyed$.next(true);
    this.destroyed$.complete();
  }

  isEmptyObject(obj) {
    return obj && Object.keys(obj).length === 0;
  }
}
