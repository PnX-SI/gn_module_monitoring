import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from "@angular/core";
import { GN2CommonModule } from "@geonature_common/GN2Common.module";
import { Routes, RouterModule } from "@angular/router";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { ReactiveFormsModule } from "@angular/forms";
import { HttpClient } from "@angular/common/http";
import { HttpClientXsrfModule } from "@angular/common/http";

// Service
import { DataMonitoringObjectService } from "./services/data-monitoring-object.service";
import { DataUtilsService } from "./services/data-utils.service";
import { CacheService } from "./services/cache.service";
import { MonitoringObjectService } from "./services/monitoring-object.service";
import { ConfigService } from "./services/config.service";
import { UploadService } from "./components/upload-media/upload.service";

// Component
import { BreadcrumbsComponent } from "./components/breadcrumbs/breadcrumbs.component";
import { ModulesComponent } from "./components/modules/modules.component";
import { UploadMediaComponent } from "./components/upload-media/upload-media.component";
import { MonitoringObjectComponent } from "./components/monitoring-object/monitoring-object.component";
import { DrawFormComponent } from "./components/draw-form/draw-form.component";
import { ModalMsgComponent } from "./components/modal-msg/modal-msg.component";
import { MonitoringMapComponent } from "./components/monitoring-map/monitoring-map.component";
import { MonitoringFormComponent } from "./components/monitoring-form/monitoring-form.component";
import { MonitoringChoixSiteComponent } from "./components/monitoring-form/choix-site/choix-site.component";
import { MonitoringListComponent } from "./components/monitoring-lists/monitoring-lists.component";
import { MonitoringPropertiesComponent } from "./components/monitoring-properties/monitoring-properties.component";
import { MediasComponent } from "./components/medias/medias.component";
import { MonitoringDatatableComponent } from "./components/monitoring-datatable/monitoring-datatable.component";

import { MonitoringChoixAireComponent } from "./components/monitoring-form/choix-aire/choix-aire.component";

import {
  MatSlideToggleModule,
  MatFormFieldModule,
  MatAutocompleteModule,
  MatSelectModule,
  MatInputModule,
} from "@angular/material";

import { NgxMatSelectSearchModule } from 'ngx-mat-select-search';


// my module routing
const routes: Routes = [
  /** modules  */
  { path: "", component: ModulesComponent },

  /** module  */
  // { path: 'module/:modulePath', component: MonitoringObjectComponent },
  /** create module */
  // { path: 'module', component: MonitoringObjectComponent },

  /** object */
  {
    path: "object/:modulePath/:objectType/:id",
    component: MonitoringObjectComponent,
  },
  /** create object */
  {
    path: "create_object/:modulePath/:objectType/:parentId",
    component: MonitoringObjectComponent,
  },
];

@NgModule({
  declarations: [
    BreadcrumbsComponent,
    ModulesComponent,
    UploadMediaComponent,
    MonitoringObjectComponent,
    DrawFormComponent,
    ModalMsgComponent,
    MonitoringMapComponent,
    MonitoringFormComponent,
    MonitoringListComponent,
    MonitoringPropertiesComponent,
    MediasComponent,
    MonitoringDatatableComponent,
    MonitoringChoixSiteComponent,
    MonitoringChoixAireComponent,
  ],
  imports: [
    GN2CommonModule,
    RouterModule.forChild(routes),
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatSlideToggleModule,
    MatFormFieldModule,
    MatAutocompleteModule,
    MatSelectModule,
    MatInputModule,
    NgxMatSelectSearchModule,
    HttpClientXsrfModule.withOptions({
      headerName: "token",
    }),
  ],
  providers: [
    HttpClient,
    CacheService,
    DataMonitoringObjectService,
    DataUtilsService,
    ConfigService,
    MonitoringObjectService,
    UploadService,
  ],
  bootstrap: [ModulesComponent],
  schemas: [
    // CUSTOM_ELEMENTS_SCHEMA
  ],
})
export class GeonatureModule {}
