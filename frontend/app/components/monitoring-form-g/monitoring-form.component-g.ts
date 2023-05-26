import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { tap, mergeMap, map } from 'rxjs/operators';
import { ActivatedRoute } from '@angular/router';
import { Router } from '@angular/router';
import { DynamicFormService } from '@geonature_common/form/dynamic-form-generator/dynamic-form.service';
import { CommonService } from '@geonature_common/service/common.service';

import { IDataForm } from '../../interfaces/form';
import { ApiGeomService } from '../../services/api-geom.service';
import { ConfigJsonService } from '../../services/config-json.service';
import { FormService } from '../../services/form.service';
import { IExtraForm } from '../../interfaces/object';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'pnx-monitoring-form-g',
  templateUrl: './monitoring-form.component-g.html',
  styleUrls: ['./monitoring-form.component-g.css'],
})
export class MonitoringFormComponentG implements OnInit {
  @Input() currentUser;

  @Input() objForm: FormGroup;

  // @Input() obj: any;
  @Output() objChanged = new EventEmitter<Object>();

  @Input() objectsStatus;
  @Output() objectsStatusChange = new EventEmitter<Object>();

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() sites: {};
  @Input() apiService: ApiGeomService;
  @Input() isExtraForm: boolean = false;

  extraForm: IExtraForm;
  hideForm: boolean = false;
  dataForm: IDataForm;
  searchSite = '';

  obj: any;
  objFormsDefinition;

  meta: {};

  public bSaveSpinner = false;
  public bSaveAndAddChildrenSpinner = false;
  public bDeleteSpinner = false;
  public bDeleteModal = false;
  public bChainInput = false;
  public bAddChildren = false;
  public chainShow = [];

  public queryParams = {};

  joinObs: any;

  constructor(
    private _formBuilder: FormBuilder,
    private _route: ActivatedRoute,
    private _configService: ConfigJsonService,
    private _commonService: CommonService,
    private _dynformService: DynamicFormService,
    private _formService: FormService,
    private _router: Router
  ) {}

  ngOnInit() {
    this._formService.currentData
      .pipe(
        tap((data) => {
          this.obj = data;
          this.obj.bIsInitialized = true;
          this.obj.id = this.obj[this.obj.pk];
        }),
        mergeMap((data: any) => this._configService.init(data.moduleCode)),
        mergeMap(() => {
          return this._formService.currentExtraFormCtrl.pipe(
            map((frmCtrl) => {
              return frmCtrl;
            })
          );
        }),
        mergeMap((frmCtrl) => {
          return this.apiService.getConfig().pipe(
            map((prop) => {
              return { frmCtrl, prop: prop };
            })
          );
        })
      )
      .subscribe((data) => {
        this.initObj(data.prop);
        this.isExtraForm ? this.addExtraFormCtrl(data.frmCtrl) : null;
        this.isExtraForm ? this.checkValidExtraFormCtrl() : null;

        this.obj.config = this._configService.configModuleObject(
          this.obj.moduleCode,
          this.obj.objectType
        );
        this.queryParams = this._route.snapshot.queryParams || {};
        this.bChainInput = this._configService.frontendParams().bChainInput;

        const schema = this._configService.schema(this.obj.moduleCode, this.obj.objectType);

        this.obj[this.obj.moduleCode] = schema;

        this.obj.specific == undefined ? (this.obj.specific = {}) : null;
        if (Object.keys(this.obj.specific).length !== 0) {
          Object.assign(schema, this.obj.specific);
        }


        // meta pour les parametres dynamiques
        // ici pour avoir acces aux nomenclatures
        this.meta = {
          // nomenclatures: this._dataUtilsService.getDataUtil('nomenclature'),
          // dataset: this._dataUtilsService.getDataUtil('dataset'),
          // id_role: this.currentUser.id_role,
          bChainInput: this.bChainInput,
          parents: this.obj.parents,
        };

        this.objFormsDefinition = this._dynformService
          .formDefinitionsdictToArray(schema, this.meta)
          .filter((formDef) => formDef.type_widget)
          .sort((a, b) => {
            // medias à la fin
            return a.attribut_name === 'medias' ? +1 : b.attribut_name === 'medias' ? -1 : 0;
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
          this.objFormsDefinition.sort((a, b) => {
            let indexA = displayProperties.findIndex((e) => e == a.attribut_name);
            let indexB = displayProperties.findIndex((e) => e == b.attribut_name);
            return indexB - indexA;
          });
        }

        // champs patch pour simuler un changement de valeur et déclencher le recalcul des propriété
        // par exemple quand bChainInput change
        this.objForm.addControl('patch_update', this._formBuilder.control(0));

        this.initForm();
      });
  }

  /** pour réutiliser des paramètres déjà saisis */
  keepDefinitions() {
    return this.objFormsDefinition.filter((def) =>
      this._configService
        .configModuleObjectParam(this.obj.moduleCode, this.obj.objectType, 'keep')
        .includes(def.attribut_name)
    );
  }

  setQueryParams() {
    // par le biais des parametre query de route on donne l'id du ou des parents
    // permet d'avoir un 'tree' ou un objet est sur plusieurs branches
    // on attend des ids d'où test avec parseInt
    for (const key of Object.keys(this.queryParams)) {
      const strToInt = parseInt(this.queryParams[key]);
      if (strToInt != NaN) {
        this.obj.properties[key] = strToInt;
      }
    }
  }

  /** initialise le formulaire quand le formulaire est prêt ou l'object est prêt */
  initForm() {
    if (!(this.objForm && this.obj.bIsInitialized)) {
      return;
    }

    this.setQueryParams();
    // pour donner la valeur de l'objet au formulaire
    this._formService.formValues(this.obj).subscribe((formValue) => {
      this.objForm.patchValue(formValue);
      this.setDefaultFormValue();
      this.dataForm = formValue;
      // reset geom ?
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
    this.objForm.patchValue({ geometry: null });
    this.initForm();
    // };
  }

  /** Pour donner des valeurs par defaut si la valeur n'est pas définie
   * id_digitiser => current_user.id_role
   * id_inventor => current_user.id_role
   * date => today
   */
  setDefaultFormValue() {
    const value = this.objForm.value;
    const date = new Date();
    const defaultValue = {
      // id_digitiser: value["id_digitiser"] || this.currentUser.id_role,
      // id_inventor: value["id_inventor"] || this.currentUser.id_role,
      first_use_date: value['first_use_date'] || {
        year: date.getUTCFullYear(),
        month: date.getUTCMonth() + 1,
        day: date.getUTCDate(),
      },
    };
    this.objForm.patchValue(defaultValue);
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
    //
    const urlSegment = [objectType, id].filter((s) => !!s);
    const urlPathDetail = [this.obj.urlRelative].concat(urlSegment).join('/');
    this.objChanged.emit(this.obj);
    this.bEditChange.emit(false);
    this.obj.urlRelative ? this._router.navigateByUrl(urlPathDetail) : null;
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToParent() {
    this.bEditChange.emit(false); // patch bug navigation
    this._router.navigate(['..'], { relativeTo: this._route });
  }



  msgToaster(action) {
    // return `${action} ${this.obj.labelDu()} ${this.obj.description()} effectuée`.trim();
    return `${action}  effectuée`.trim();
  }

  /** TODO améliorer site etc.. */
  onSubmit() {
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
    if (this.obj.id) {
      this.bEditChange.emit(false);
    } else {
      this.navigateToParent();
    }
  }

  onDelete() {
    this.bDeleteSpinner = true;
    this._commonService.regularToaster('info', this.msgToaster('Suppression'));
    // : this.obj.post(this.objForm.value);
    this.apiService.delete(this.obj.id).subscribe((del) => {
      this.bDeleteSpinner = this.bDeleteModal = false;
      this.objChanged.emit(this.obj);
      setTimeout(() => {
        this.navigateToParent();
      }, 100);
    });
  }

  onObjFormValueChange(event) {
    // let {id_module,medias, ...rest} = this.objForm.value;
    // this.dataForm = rest
    this.dataForm = this.objForm.value;
    const change = this._configService.change(this.obj.moduleCode, this.obj.objectType);
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({ objForm: this.objForm, meta: this.meta });
    }, 100);
  }

  procesPatchUpdateForm() {
    this.objForm.patchValue({
      patch_update: this.objForm.value.patch_update + 1,
    });
  }

  /** bChainInput gardé dans config service */
  bChainInputChanged() {
    for (const formDef of this.objFormsDefinition) {
      formDef.meta.bChainInput = this.bChainInput;
    }
    this._configService.setFrontendParams('bChainInput', this.bChainInput);
    // patch pour recalculers
    this.procesPatchUpdateForm();
  }

  addExtraFormCtrl(frmCtrl: IExtraForm) {
    if (frmCtrl.frmName in this.objForm.controls) {
      this.objForm.setControl(frmCtrl.frmName, frmCtrl.frmCtrl);
    } else {
      this.objForm.addControl(frmCtrl.frmName, frmCtrl.frmCtrl);
    }

    this.extraForm = frmCtrl;
  }

  checkValidExtraFormCtrl() {
    if (
      this.extraForm.frmName in this.objForm.controls &&
      this.objForm.get(this.extraForm.frmName).value != null &&
      this.objForm.get(this.extraForm.frmName).value.length != 0
    ) {
      this.hideForm = false;
      this.objForm.valid;
    } else {
      this.hideForm = true;
    }
  }

  getConfigFromBtnSelect(event) {
    // TODO: Ajout de tous les id_parents ["id_sites_groups" etc ] dans l'objet obj.dataComplement
    // Check if specific and dataComplement already exist
    this.obj.specific ? null : (this.obj.specific = {});
    this.obj.dataComplement ? null : (this.obj.dataComplement = {});

    Object.entries(event).forEach(([key, value]) => {
      if (this.obj.dataComplement[key] && key != 'types_site') {
        return;
      }
      if (event[key].config != undefined) {
        if (Object.keys(event[key].config).length !== 0) {
          Object.assign(this.obj.specific, event[key].config.specific);
          if ('keep' in event[key].config) {
            this.obj.config.keep ? null : (this.obj.config.keep = []);
            !this.obj.config.keep.includes(event[key].config.keep)
              ? this.obj.config.keep.push(...event[key].config.keep)
              : null;
          }
        }
        this.obj.dataComplement[key] = value;
      } else {
        this.obj.dataComplement[key] ? null : (this.obj.dataComplement[key] = []);
        this.obj.dataComplement[key] = event[key];
      }
    });

    this._formService.dataToCreate(this.obj, this.obj.urlRelative);
  }

  initObj(prop) {
    // this.apiService.getConfig().subscribe(prop => this.obj['properties'] = prop)
    this.obj['properties'] = prop;
    Object.entries(this.obj).forEach(([key, value]) => {
      if (key != 'properties' && key in this.obj['properties']) {
        this.obj['properties'][key] = value;
      }
    });
    this.obj.resolvedProperties = this._configService.setResolvedProperties(this.obj);
  }
}
