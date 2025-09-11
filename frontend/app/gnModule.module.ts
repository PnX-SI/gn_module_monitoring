import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { GN2CommonModule } from '@geonature_common/GN2Common.module';
import { Routes, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { HttpClientXsrfModule } from '@angular/common/http';

// Service
import { DataMonitoringObjectService } from './services/data-monitoring-object.service';
import { DataUtilsService } from './services/data-utils.service';
import { CacheService } from './services/cache.service';
import { MonitoringObjectService } from './services/monitoring-object.service';
import { ConfigService } from './services/config.service';
import { ConfigJsonService } from './services/config-json.service';

// Component
import { BreadcrumbsComponent } from './components/breadcrumbs/breadcrumbs.component';
import { ModulesComponent } from './components/modules/modules.component';
import { MonitoringObjectComponent } from './components/monitoring-object/monitoring-object.component';
import { DrawFormComponent } from './components/draw-form/draw-form.component';
import { ModalMsgComponent } from './components/modal-msg/modal-msg.component';
import { MonitoringMapComponent } from './components/monitoring-map/monitoring-map.component';
import { MonitoringFormComponent } from './components/monitoring-form/monitoring-form.component';
import { MonitoringListComponent } from './components/monitoring-lists/monitoring-lists.component';
import { MonitoringPropertiesComponent } from './components/monitoring-properties/monitoring-properties.component';
import { MonitoringDatatableComponent } from './components/monitoring-datatable/monitoring-datatable.component';
import { MonitoringDatatableGComponent } from './components/monitoring-datatable-g/monitoring-datatable-g.component';

import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatChipsModule } from '@angular/material/chips';
import { MonitoringSitesGroupsComponent } from './components/monitoring-sitesgroups/monitoring-sitesgroups.component';
import { DataTableService } from './services/data-table.service';
import { MonitoringPropertiesGComponent } from './components/monitoring-properties-g/monitoring-properties-g.component';
import { GeoJSONService } from './services/geojson.service';
import { MonitoringSitesgroupsDetailComponent } from './components/monitoring-sitesgroups-detail/monitoring-sitesgroups-detail.component';

import { MonitoringMapListComponent } from './components/monitoring-map-list/monitoring-map-list.component';
import { FormService } from './services/form.service';
import { ObjectService } from './services/object.service';
import { PermissionService } from './services/permission.service';
import {
  SitesGroupService,
  SitesService,
  ApiGeomService,
  VisitsService,
} from './services/api-geom.service';
import { MonitoringSitesGroupsCreateComponent } from './components/monitoring-sitesgroups-create/monitoring-sitesgroups-create.component';
import { MonitoringSitesCreateComponent } from './components/monitoring-sites-create/monitoring-sites-create.component';
import { BtnSelectComponent } from './components/btn-select/btn-select.component';
import { MonitoringSitesDetailComponent } from './components/monitoring-sites-detail/monitoring-sites-detail.component';
import { OptionListButtonComponent } from './components/option-list-btn/option-list-btn.component';
import { MatErrorMessagesDirective } from './utils/matErrorMessages.directive';
import { SitesGroupsResolver } from './resolver/sites-groups.resolver';
import { CreateSiteResolver } from './resolver/create-site.resolver';
import { PageNotFoundComponent } from './components/page-not-found/page-not-found.component';
import { ObjectsPermissionMonitorings } from './enum/objectPermission';

import { Popup } from './utils/popup';
import { ListService } from './services/list.service';
import { CreateSitesGroupsResolver } from './resolver/create-sites-groups-resolver';
import { DetailSitesGroupsResolver } from './resolver/detail-sites-groups-resolver';
import { DetailSitesResolver } from './resolver/detail-sites-resolver';
import { MapListResolver } from './resolver/map-list-resolver';

// my module routing
const routes: Routes = [
  /** modules  */
  { path: '', component: ModulesComponent },
  {
    path: 'object/:moduleCode/sites_group',
    component: MonitoringMapListComponent,
    resolve: {
      data: MapListResolver,
    },
    children: [
      {
        path: '',
        component: MonitoringSitesGroupsComponent,
        resolve: {
          data: SitesGroupsResolver,
        },
        runGuardsAndResolvers: 'always',
      },
      {
        path: 'create',
        component: MonitoringSitesGroupsCreateComponent,
        resolve: {
          createSitesGroups: CreateSitesGroupsResolver,
        },
      },
      {
        path: ':id',
        children: [
          {
            path: '',
            component: MonitoringSitesgroupsDetailComponent,
            resolve: {
              detailSitesGroups: DetailSitesGroupsResolver,
            },
          },
          {
            path: 'create',
            component: MonitoringSitesCreateComponent,
            resolve: {
              createSite: CreateSiteResolver,
            },
          },
          {
            path: 'site/:id',
            component: MonitoringSitesDetailComponent,
            resolve: {
              detailSites: DetailSitesResolver,
            },
          },
        ],
      },
    ],
  },
  {
    path: 'object/:moduleCode/site',
    component: MonitoringMapListComponent,
    resolve: {
      data: MapListResolver,
    },
    children: [
      {
        path: '',
        component: MonitoringSitesGroupsComponent,
        resolve: {
          data: SitesGroupsResolver,
        },
        runGuardsAndResolvers: 'always',
      },
      {
        path: 'create',
        component: MonitoringSitesCreateComponent,
        resolve: {
          createSite: CreateSiteResolver,
        },
      },
      {
        path: ':id',
        component: MonitoringSitesDetailComponent,
        resolve: {
          detailSites: DetailSitesResolver,
        },
      },
    ],
  },
  {
    path: 'object/:moduleCode/:objectType/:id',
    component: MonitoringObjectComponent,
  },
  {
    path: 'create_object/:moduleCode/:objectType',
    component: MonitoringObjectComponent,
  },
  { path: 'not-found', component: PageNotFoundComponent },
  { path: '**', redirectTo: 'not-found' },
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
    MonitoringSitesgroupsDetailComponent,
    MonitoringDatatableGComponent,
    MonitoringPropertiesGComponent,
    MonitoringSitesGroupsCreateComponent,
    MonitoringSitesCreateComponent,
    BtnSelectComponent,
    MonitoringSitesDetailComponent,
    OptionListButtonComponent,
    MatErrorMessagesDirective,
    PageNotFoundComponent,
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
    MatChipsModule,
    HttpClientXsrfModule.withOptions({
      headerName: 'token',
    }),
  ],
  providers: [
    HttpClient,
    CacheService,
    DataMonitoringObjectService,
    DataUtilsService,
    ConfigService,
    ConfigJsonService,
    MonitoringObjectService,
    DataTableService,
    SitesGroupService,
    SitesService,
    GeoJSONService,
    ListService,
    FormService,
    ObjectService,
    ApiGeomService,
    VisitsService,
    SitesGroupsResolver,
    CreateSiteResolver,
    CreateSitesGroupsResolver,
    PermissionService,
    Popup,
  ],
  bootstrap: [ModulesComponent],
  schemas: [
    // CUSTOM_ELEMENTS_SCHEMA
  ],
})
export class GeonatureModule {}
