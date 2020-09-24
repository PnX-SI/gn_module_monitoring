import { Component, OnInit, Input, Output, EventEmitter } from "@angular/core";
import { FormGroup, FormBuilder, Validators } from "@angular/forms";
import { MonitoringObject } from "../../class/monitoring-object";
import { Utils } from "../../utils/utils";
import { Router } from "@angular/router";
import { ConfigService } from "../../services/config.service";

import { mergeMap } from "@librairies/rxjs/operators";

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

  @Input() aires: {};

  searchSite = "";

  objFormsDefinition;

  keepNames = [];

  public bSaveSpinner = false;
  public bSaveAddSpinner = false;
  public bDeleteSpinner = false;
  public bDeleteModal = false;
  public bChainInput = false;
  public bAddChildren = false;

  constructor(
    private _formBuilder: FormBuilder,
    private _router: Router,
    private _configService: ConfigService
  ) {}

  ngOnInit() {
    this._configService
      .init(this.obj.modulePath)
      .pipe(
        mergeMap(() => {
          this.bChainInput = this._configService.frontendParams()[
            "bChainInput"
          ];
          const schema = this.obj.schema();

          // init objFormsDefinition
          this.objFormsDefinition = Object.keys(schema)
            .filter((attribut_name) => schema[attribut_name].type_widget)
            .map((attribut_name) => {
              const elem = schema[attribut_name];
              elem["attribut_name"] = attribut_name;
              return elem;
            });
          return this.obj.formValues();
        })
      )
      .subscribe((formValues) => {
        // set geometry
        if (this.obj.config["geometry_type"]) {
          this.objForm.addControl(
            "geometry",
            this._formBuilder.control("", Validators.required)
          );
        }
        this.setFormValue(formValues);
      });
  }

  keepDefinitions() {
    return this.objFormsDefinition.filter((def) =>
      this.obj.configParam("keep").includes(def.attribut_name)
    );
  }

  isFormReady() {
    let schemaFormSize = this.objFormsDefinition.filter(
      (elem) => elem.type_widget
    ).length;
    if (this.obj.config["geometry_type"]) {
      schemaFormSize += 1;
    }
    const formSize = Utils.dictSize(this.objForm.controls);
    return schemaFormSize === formSize;
  }

  setFormValue(formValue) {
    const objFormChangeSubscription = this.objForm.valueChanges.subscribe(
      () => {
        if (this.isFormReady()) {
          objFormChangeSubscription.unsubscribe();
          this.objForm.setValue(formValue);
          this.setDefaultFormValue();
        }
      }
    );
    // emit change programmatically
    this.objForm.updateValueAndValidity({ onlySelf: false, emitEvent: true });
  }

  resetObjForm() {
    const keep = {};
    for (const key of this.keepNames) {
      keep[key] = this.obj.properties[key];
    }

    console.log("keep", keep);

    const parentId = this.obj.parentId;
    this.obj = new MonitoringObject(
      this.obj.modulePath,
      this.obj.objectType,
      null,
      this.obj.monitoringObjectService()
    );
    this.obj.properties[this.obj.configParam("id_field_Name")] = null;
    this.obj.parentId = parentId;
    this.obj
      .get(0)
      .pipe(
        mergeMap(() => {
          this.obj.bIsInitialized = true;
          for (const key of this.keepNames) {
            this.obj.properties[key] = keep[key];
          }
          return this.obj.formValues();
        })
      )
      .subscribe((formValue) => {
        this.setFormValue(formValue);
        // this.objChanged.emit(this.obj);
      });
  }

  setDefaultFormValue() {
    const values = this.objForm.value;
    const defaultValues = {};

    defaultValues["id_digitiser"] =
      values["id_digitiser"] || this.currentUser.id_role;
    this.objForm.patchValue(defaultValues);
  }

  navigateToAddChildren() {
    this.bEditChange.emit(false);
    this._router.navigate([
      "/",
      this._configService.frontendModuleMonitoringUrl(),
      "create_object",
      this.obj.modulePath,
      this.obj.uniqueChildrenName(),
      this.obj.id,
    ]);
  }

  navigateToDetail() {
    this.bEditChange.emit(false);
    this._router.navigate([
      "/",
      this._configService.frontendModuleMonitoringUrl(),
      "object",
      this.obj.modulePath,
      this.obj.objectType,
      this.obj.id,
    ]);
  }

  navigateToParent() {
    this.bEditChange.emit(false);
    if (this.obj.objectType.includes("module")) {
      this._router.navigate([
        "/",
        this._configService.frontendModuleMonitoringUrl(),
        "object",
        this.obj.modulePath,
        "module",
        this.obj.id,
      ]);
    } else {
      this._router.navigate([
        "/",
        this._configService.frontendModuleMonitoringUrl(),
        "object",
        this.obj.modulePath,
        this.obj.parentType(),
        this.obj.parentId,
      ]);
    }
  }

  reload_create_route() {
    this._router.navigate(["/"]);
    setTimeout(() => {
      this._router.navigate([
        "/",
        this._configService.frontendModuleMonitoringUrl(),
        "create_object",
        this.obj.modulePath,
        this.obj.objectType,
        this.obj.parentId,
      ]);
    }, 100);
  }

  testChoixSite() {
    const bCreation = !this.obj.id;
    const bChoixSite =
      this.obj.schema()["id_base_site"] &&
      this.obj.schema()["id_base_site"].type_widget === "site";
    return bCreation && bChoixSite && this.bChainInput;
  }

  onSubmit() {

    this.bSaveSpinner = !this.bChainInput;
    this.bSaveAddSpinner = this.bChainInput;

    // cas choix site
    if (this.testChoixSite()) {
      this.obj.parentId = this.objForm.value["id_base_site"];
    }

    const action = this.obj.id
      ? this.obj.patch(this.objForm.value)
      : this.obj.post(this.objForm.value);
    const actionLabel = this.obj.id ? "Modification" : "Création";
    action.subscribe((objData) => {
      console.log(
        "info",
        `${actionLabel} de ${this.obj.configParam("label")} ${
          this.obj.id
        } effectué`
      );
      this.bSaveSpinner = this.bSaveAddSpinner = false;
      this.objChanged.emit(this.obj);
      if (this.bChainInput) {
        this.resetObjForm();
      } else if (this.bAddChildren){
        this.navigateToAddChildren()
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
    } supprimé. parent ${this.obj.parentType()} ${this.obj.parentId}`;
    console.log(msg_delete);

    this.obj.delete().subscribe((objData) => {
      this.bDeleteSpinner = this.bDeleteModal = false;
      this.objChanged.emit(this.obj);
      this.navigateToParent();
    });
  }

  bChainInputChanged() {
    this._configService.setFrontendParams("bChainInput", this.bChainInput);
  }
}
