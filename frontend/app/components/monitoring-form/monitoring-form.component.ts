import { mergeMap } from "@librairies/rxjs/operators";
import { Component, OnInit, Input, Output, EventEmitter } from "@angular/core";
import { FormGroup, FormBuilder, Validators } from "@angular/forms";
import { MonitoringObject } from "../../class/monitoring-object";
import { Router } from "@angular/router";
import { ConfigService } from "../../services/config.service";
import { DataUtilsService } from "../../services/data-utils.service";
import { CommonService } from "@geonature_common/service/common.service";
import { DynamicFormService } from "@geonature_common/form/dynamic-form-generator/dynamic-form.service";
import { ActivatedRoute } from "@angular/router";

@Component({
  selector: "pnx-monitoring-form",
  templateUrl: "./monitoring-form.component.html",
  styleUrls: ["./monitoring-form.component.css"],
})
export class MonitoringFormComponent implements OnInit {
  @Input() currentUser;

  @Input() objForm: FormGroup;

  @Input() obj: MonitoringObject;
  @Output() objChanged = new EventEmitter<MonitoringObject>();

  @Input() objectsStatus;
  @Output() objectsStatusChange = new EventEmitter<Object>();

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() sites: {};

  searchSite = "";

  objFormsDefinition;

  meta: {};

  keepNames = [];

  public bSaveSpinner = false;
  public bSaveAndAddChildrenSpinner = false;
  public bDeleteSpinner = false;
  public bDeleteModal = false;
  public bChainInput = false;
  public bAddChildren = false;

  public queryParams = {};

  constructor(
    private _formBuilder: FormBuilder,
    private _router: Router,
    private _route: ActivatedRoute,
    private _configService: ConfigService,
    private _commonService: CommonService,
    private _dataUtilsService: DataUtilsService,
    private _dynformService: DynamicFormService
  ) {}

  ngOnInit() {
    this._configService
      .init(this.obj.moduleCode)
      .mergeMap(() => {
        return this._route.queryParamMap;
      })
      .subscribe((queryParams) => {
        this.queryParams = queryParams["params"] || {};
        this.bChainInput = this._configService.frontendParams()["bChainInput"];
        const schema = this.obj.schema();
        // init objFormsDefinition

        // meta pour les parametres dynamiques
        // ici pour avoir acces aux nomenclatures
        this.meta = {
            nomenclatures: this._dataUtilsService.getNomenclatures(),
            id_role: this.currentUser.id_role,
        }
        this.objFormsDefinition = this._dynformService
          .formDefinitionsdictToArray(schema, this.meta)
          .filter((formDef) => formDef.type_widget)
          .sort((a, b) => {
            return a.attribut_name === "medias"
              ? +1
              : b.attribut_name === "medias"
              ? -1
              : 0;
          }); // medias à la fin

        // set geometry
        if (this.obj.config["geometry_type"]) {
          this.objForm.addControl(
            "geometry",
            this._formBuilder.control("", Validators.required)
          );
        }
        this.initForm();
      });
  }

  /** pour réutiliser des paramètres déjà saisis */
  keepDefinitions() {
    return this.objFormsDefinition.filter((def) =>
      this.obj.configParam("keep").includes(def.attribut_name)
    );
  }

  setQueryParams() {
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
    this.obj.formValues().subscribe((formValue) => {
      this.objForm.patchValue(formValue);
      this.setDefaultFormValue();
    });
  }

  resetObjForm() {
    const keep = {};
    for (const key of this.keepNames) {
      keep[key] = this.obj.properties[key];
    }

    // TODO à faire comme il faut (popup config pour les valeurs à garder)

    // this.obj = new MonitoringObject(
    //   this.obj.moduleCode,
    //   this.obj.objectType,
    //   null,
    //   this.obj.monitoringObjectService()
    // );

    this.obj.properties[this.obj.configParam("id_field_Name")] = null;
    // this.obj.parentId = parentId;
    this.obj.get(0).subscribe(() => {
      this.obj.bIsInitialized = true;
      for (const key of this.keepNames) {
        this.obj.properties[key] = keep[key];
      }
      this.initForm();
    });
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
      id_digitiser: value["id_digitiser"] || this.currentUser.id_role,
      id_inventor: value["id_inventor"] || this.currentUser.id_role,
      first_use_date: value['first_use_date'] || {
          year: date.getUTCFullYear(),
          month: date.getUTCMonth() + 1,
          day: date.getUTCDate(),
        }
      }
    console.log(defaultValue)
    this.objForm.patchValue(defaultValue);
  }

  /**
   * TODO faire des fonctions dans monitoring objet (ou moniotring objet service pour naviguer
   */

  /**
   * Valider et renseigner les enfants
   */
  navigateToAddChildren() {
    const queryParamsAddChildren = {};
    queryParamsAddChildren[this.obj.idFieldName()] = this.obj.id;
    queryParamsAddChildren["parents_path"] = this.obj.parentsPath.concat(
      this.obj.objectType
    );
    this.bEditChange.emit(false);
    this._router.navigate(
      [
        "/",
        this._configService.frontendModuleMonitoringUrl(),
        "create_object",
        this.obj.moduleCode,
        this.obj.uniqueChildrenType(),
      ],
      {
        queryParams: queryParamsAddChildren,
      }
    );
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToDetail() {
    this.bEditChange.emit(false); // patch bug navigation
    this._router.navigate(
      [
        "/",
        this._configService.frontendModuleMonitoringUrl(),
        "object",
        this.obj.moduleCode,
        this.obj.objectType,
        this.obj.id,
      ],
      {
        queryParams: {
          parents_path: this.obj.parentsPath,
        },
      }
    );
  }

  /**
   * Valider et aller à la page de l'objet
   */
  navigateToParent() {
    this.bEditChange.emit(false); // patch bug navigation

    // cas module
    if (this.obj.objectType.includes("module")) {
      this._router.navigate([
        "/",
        this._configService.frontendModuleMonitoringUrl(),
        "object",
        this.obj.moduleCode,
        "module",
        this.obj.id,
      ]);

      // autres cas
    } else {
      const parentType =  this.obj.parentType();
      this.obj.parentsPath.pop();
      const parent = new MonitoringObject(
        this.obj.moduleCode,
        parentType,
        null,
        this.obj._objService
      );
      const parentId = this.obj.properties[parent.idFieldName()];
      this._router.navigate(
        [
          "/",
          this._configService.frontendModuleMonitoringUrl(),
          "object",
          this.obj.moduleCode,
          parentType,
          parentId,
        ],
        {
          queryParams: {
            parents_path: this.obj.parentsPath,
          },
        }
      );
    }
  }

  /** TODO remove */
  // reload_create_route() {
  //   this._router.navigate(['/']);
  //   setTimeout(() => {
  //     this._router.navigate([
  //       '/',
  //       this._configService.frontendModuleMonitoringUrl(),
  //       'create_object',
  //       this.obj.moduleCode,
  //       this.obj.objectType,
  //       this.obj.parentId,
  //     ]);
  //   }, 100);
  // }

  /** TODO améliorer */
  testChoixSite() {
    const bCreation = !this.obj.id;
    const bChoixSite =
      this.obj.schema()["id_base_site"] &&
      this.obj.schema()["id_base_site"].type_widget === "site";
    return bCreation && bChoixSite && this.bChainInput;
  }

  /** TODO améliorer site etc.. */
  onSubmit() {
    // cas choix site
    // if (this.testChoixSite()) {
    //   this.obj.parentId = this.objForm.value["id_base_site"];
    // }
    const action = this.obj.id
      ? this.obj.patch(this.objForm.value)
      : this.obj.post(this.objForm.value);
    const actionLabel = this.obj.id ? "Modification" : "Création";
    action.subscribe((objData) => {
      this._commonService.regularToaster(
        "success",
        `${actionLabel} de ${this.obj.configParam("label")} ${
          this.obj.id
        } effectuée`
      );
      this.bSaveSpinner = this.bSaveAndAddChildrenSpinner = false;
      this.objChanged.emit(this.obj);

      /** si c'est un module : reset de la config */
      if (this.obj.objectType === "module") {
        this._configService.loadConfig(this.obj.moduleCode).subscribe();
      }

      if (this.bChainInput) {
        this.resetObjForm();
      } else if (this.bAddChildren) {
        this.navigateToAddChildren();
      } else {
        this.navigateToDetail();
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
    const msg_delete = `${this.obj.template["label"]} ${
      this.obj.id
    } supprimé. parent ${this.obj.parentType()} ${this.obj.parentId()}`;
    this._commonService.regularToaster("info", msg_delete);

    this.obj.delete().subscribe((objData) => {
      this.bDeleteSpinner = this.bDeleteModal = false;
      this.obj.deleted = true;
      this.objChanged.emit(this.obj);

      setTimeout(() => {
        this.navigateToParent();
      }, 100)
    });
  }

  onObjFormValueChange(event) {
    const change = this.obj.change();
    if (!change) {
      return;
    }
    setTimeout(() => {
      change({objForm:this.objForm, meta: this.meta})
    }, 100);
  }

  /** bChainInput gardé dans config service */
  bChainInputChanged() {
    this._configService.setFrontendParams("bChainInput", this.bChainInput);
  }
}
