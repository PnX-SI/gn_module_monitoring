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

// Component
import { BreadcrumbsComponent } from "./components/breadcrumbs/breadcrumbs.component";
import { ModulesComponent } from "./components/modules/modules.component";
import { MonitoringObjectComponent } from "./components/monitoring-object/monitoring-object.component";
import { DrawFormComponent } from "./components/draw-form/draw-form.component";
import { ModalMsgComponent } from "./components/modal-msg/modal-msg.component";
import { MonitoringMapComponent } from "./components/monitoring-map/monitoring-map.component";
import { MonitoringFormComponent } from "./components/monitoring-form/monitoring-form.component";
import { MonitoringListComponent } from "./components/monitoring-lists/monitoring-lists.component";
import { MonitoringPropertiesComponent } from "./components/monitoring-properties/monitoring-properties.component";
import { MonitoringDatatableComponent } from "./components/monitoring-datatable/monitoring-datatable.component";
import { MonitoringDatatableGComponent } from "./components/monitoring-datatable-g/monitoring-datatable-g.component";

import { MatSlideToggleModule } from "@angular/material/slide-toggle";
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatAutocompleteModule } from "@angular/material/autocomplete";
import { MatSelectModule } from "@angular/material/select";
import { MatInputModule } from "@angular/material/input";
import { MonitoringSitesGroupsComponent } from "./components/monitoring-sitesgroups/monitoring-sitesgroups.component";
import { DataTableService } from "./services/data-table.service";
import { MonitoringPropertiesGComponent } from "./components/monitoring-properties-g/monitoring-properties-g.component";
import { GeoJSONService } from "./services/geojson.service";
import { MonitoringSitesComponent } from "./components/monitoring-sites/monitoring-sites.component";
import { MonitoringMapListComponent } from "./components/monitoring-map-list/monitoring-map-list.component";
import { MonitoringFormComponentG } from "./components/monitoring-form-g/monitoring-form.component-g";
import { EditObjectService } from "./services/edit-object.service";
import { ObjectService } from "./services/object.service";
import {
  SitesGroupService,
  SitesService,
  ApiGeomService,
} from "./services/api-geom.service";
import { MonitoringSitesGroupsCreateComponent } from "./components/monitoring-sitesgroups-create/monitoring-sitesgroups-create.component";

// my module routing
const routes: Routes = [
  /** modules  */
  { path: "", component: ModulesComponent },

  /** module  */
  { path: "module/:moduleCode", component: MonitoringObjectComponent },
  /** create module */
  { path: "module", component: MonitoringObjectComponent },

  /** object */
  {
    path: "object/:moduleCode/:objectType/:id",
    component: MonitoringObjectComponent,
  },
  /** create object */
  {
    path: "create_object/:moduleCode/:objectType",
    component: MonitoringObjectComponent,
  },
  {
    path: "sites_group",
    component: MonitoringMapListComponent,
    children: [
      {
        path: "",
        component: MonitoringSitesGroupsComponent,
      },
      { path: "create", component: MonitoringSitesGroupsCreateComponent },
      {
        path: ":id",
        // Add new component here
        children: [
          {
            path: "",
            component: MonitoringSitesComponent,
          },
        ],
      },
    ],
  },
];

@NgModule({
  declarations: [
    BreadcrumbsComponent,
    ModulesComponent,
    MonitoringObjectComponent,
    DrawFormComponent,
    ModalMsgComponent,
    MonitoringMapComponent,
    MonitoringFormComponent,
    MonitoringListComponent,
    MonitoringPropertiesComponent,
    MonitoringDatatableComponent,
    MonitoringMapListComponent,
    MonitoringSitesGroupsComponent,
    MonitoringSitesComponent,
    MonitoringDatatableGComponent,
    MonitoringPropertiesGComponent,
    MonitoringFormComponentG,
    MonitoringSitesGroupsCreateComponent,
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
    DataTableService,
    SitesGroupService,
    SitesService,
    GeoJSONService,
    EditObjectService,
    ObjectService,
    ApiGeomService,
  ],
  bootstrap: [ModulesComponent],
  schemas: [
    // CUSTOM_ELEMENTS_SCHEMA
  ],
})
export class GeonatureModule {}
