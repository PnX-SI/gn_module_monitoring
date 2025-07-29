import { Injectable } from '@angular/core';
import { SitesGroupService, SitesService, IndividualsService } from '../services/api-geom.service';
import { Observable, forkJoin, of } from 'rxjs';
import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { ISite, ISitesGroup } from '../interfaces/geom';
import { IPaginated } from '../interfaces/page';
import { IobjObs } from '../interfaces/objObs';
import { concatMap, map, mergeMap } from 'rxjs/operators';
import { ConfigJsonService } from '../services/config-json.service';
import { PermissionService } from '../services/permission.service';
import { TPermission } from '../types/permission';
import { DataMonitoringObjectService } from '../services/data-monitoring-object.service';
import { resolveProperty } from '../utils/utils';
import { MonitoringObjectService } from '../services/monitoring-object.service';
import { CacheService } from '../services/cache.service';
import { ConfigService } from '../services/config.service';
import { IIndividual } from '../interfaces/individual';
import { AuthService, User } from '@geonature/components/auth/auth.service';

const LIMIT = 10;

@Injectable({ providedIn: 'root' })
export class SitesGroupsResolver
  implements
    Resolve<{
      sitesGroups: { data: IPaginated<ISitesGroup>; objConfig: IobjObs<ISitesGroup> };
      sites: { data: IPaginated<ISite>; objConfig: IobjObs<ISite> };
      individuals: { data: IPaginated<IIndividual>; objConfig: IobjObs<IIndividual> };
      route: string;
      moduleCode: string | null;
    }>
{
  currentPermission: TPermission;
  module_objects: string[] = [];

  constructor(
    private _auth: AuthService,
    public serviceSitesGroup: SitesGroupService,
    public serviceSite: SitesService,
    public serviceIndividual: IndividualsService,
    public _configJsonService: ConfigJsonService,
    public _permissionService: PermissionService,
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private router: Router,
    private _objService: MonitoringObjectService,
    private _cacheService: CacheService,
    private _configService: ConfigService
  ) {}

  resolve(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<{
    sitesGroups: { data: IPaginated<ISitesGroup>; objConfig: IobjObs<ISitesGroup> };
    sites: { data: IPaginated<ISite>; objConfig: IobjObs<ISite> };
    individuals: { data: IPaginated<IIndividual>; objConfig: IobjObs<IIndividual> };
    route: string;
    moduleCode: string | null;
  }> {
    const moduleCode = route.params.moduleCode || 'generic';
    this.serviceSitesGroup.setModuleCode(`${moduleCode}`);
    this.serviceSite.setModuleCode(`${moduleCode}`);
    this.serviceIndividual.setModuleCode(`${moduleCode}`);

    const $getPermissionMonitoring = this._dataMonitoringObjectService.getCruvedMonitoring();
    const $permissionUserObject = this._permissionService.currentPermissionObj;
    const $configSitesGroups = this.serviceSitesGroup.initConfig();
    const $configSites = this.serviceSite.initConfig();
    const $configIndividuals = this.serviceIndividual.initConfig();

    // $getPermissionMonitoring Retourne les permissions du module monitoring pas des sous_modules !!!
    const resolvedData = $getPermissionMonitoring.pipe(
      map((listObjectCruved: Object) => {
        this._permissionService.setPermissionMonitorings(listObjectCruved);
      }),
      concatMap(() =>
        $permissionUserObject.pipe(
          map((permissionObject: TPermission) => (this.currentPermission = permissionObject))
        )
      ),
      concatMap(() => this._configService.init(moduleCode)),
      concatMap(() =>
        forkJoin([$configSitesGroups, $configSites, $configIndividuals]).pipe(
          map((configs) => {
            // Récupération des permissions du module
            const module_permissions = this._configService.moduleCruved(moduleCode);

            const tree = this._configService.configModuleObject(moduleCode, 'tree');
            this.module_objects = Object.keys(tree['module']);

            // S'il n'y a pas de groupe de site  et que la page demandée est sites_group
            // redirection vers la page des sites.
            // TODO le rendre plus robuste
            if (
              !configs[0] &&
              state.url.includes('/monitorings/object/') &&
              state.url.includes('sites_group')
            ) {
              this.router.navigate(['monitorings', 'object', route.params.moduleCode, 'site']);
            }

            // Initialisation des getters et config de chaque type d'objet
            const { getter: $getSiteGroups, specificConfig: specificConfigSiteGroup } =
              this.buildObjectConfig(
                'sites_group',
                configs[0],
                module_permissions['sites_group'].R,
                this.serviceSitesGroup
              );

            const { getter: $getSites, specificConfig: specificConfigSite } =
              this.buildObjectConfig(
                'site',
                configs[1],
                module_permissions['site'].R,
                this.serviceSite
              );

            const { getter: $getIndividuals, specificConfig: specificConfigIndividual } =
              this.buildObjectConfig(
                'individual',
                configs[2],
                module_permissions['individual'].R,
                this.serviceIndividual
              );

            return forkJoin([$getSiteGroups, $getSites, $getIndividuals]).pipe(
              mergeMap(([siteGroups, sites, individuals]) => {
                const siteGroupsProcessing$ = this.buildObjectProcessing(
                  siteGroups,
                  specificConfigSiteGroup,
                  moduleCode
                );

                const sitesProcessing$ = this.buildObjectProcessing(
                  sites,
                  specificConfigSite,
                  moduleCode
                );

                const individualProcessing$ = this.buildObjectProcessing(
                  individuals,
                  specificConfigIndividual,
                  moduleCode
                );

                return forkJoin([
                  siteGroupsProcessing$,
                  sitesProcessing$,
                  individualProcessing$,
                ]).pipe(
                  map(([processedSiteGroups, processedSites, processedIndividuals]) => {
                    return {
                      sitesGroups: { data: processedSiteGroups, objConfig: configs[0] },
                      sites: { data: processedSites, objConfig: configs[1] },
                      individuals: { data: processedIndividuals, objConfig: configs[2] },
                      route: route['_urlSegment'].segments[3].path,
                      permission: this.currentPermission,
                      moduleCode,
                    };
                  })
                );
              })
            );
          }),
          mergeMap((result) => {
            return result;
          })
        )
      )
    );
    return resolvedData;
  }

  buildObjectConfig(object_type, config, permission, objectService) {
    let configSchemaObjetType = {
      sorts: [],
      specific: {},
    };
    let $getObjetTypes = of(null);
    if (this.module_objects.includes(object_type) && config) {
      configSchemaObjetType = this._configJsonService.configModuleObject(
        config.moduleCode,
        config.objectType
      );
      const sortObjetTypeInit =
        'sorts' in configSchemaObjetType
          ? {
              sort_dir: configSchemaObjetType.sorts[0]['dir'],
              sort: configSchemaObjetType.sorts[0]['prop'],
            }
          : {};
      $getObjetTypes =
        permission > 0
          ? objectService.get(1, LIMIT, sortObjetTypeInit)
          : of({ items: [], count: 0, limit: 0, page: 1 });
    }
    return {
      getter: $getObjetTypes,
      specificConfig: configSchemaObjetType?.specific,
    };
  }
  buildObjectProcessing(data, specificConfig, moduleCode) {
    const dataProcessing$ =
      data &&
      data.items &&
      data.items.length > 0 &&
      specificConfig &&
      Object.keys(specificConfig).length > 0
        ? forkJoin(
            data.items.map((dataItem) => {
              const propertyObservables = {};
              for (const attribut_name of Object.keys(specificConfig)) {
                if (dataItem.hasOwnProperty(attribut_name)) {
                  propertyObservables[attribut_name] = resolveProperty(
                    this._objService,
                    this._cacheService,
                    this._configService,
                    moduleCode,
                    specificConfig[attribut_name],
                    dataItem[attribut_name]
                  );
                }
              }
              if (Object.keys(propertyObservables).length === 0) {
                return of(dataItem);
              }
              return forkJoin(propertyObservables).pipe(
                map((resolvedProperties) => {
                  const updatedSiteGroupItem = { ...dataItem };
                  for (const attribut_name of Object.keys(resolvedProperties)) {
                    updatedSiteGroupItem[attribut_name] = resolvedProperties[attribut_name];
                  }
                  return updatedSiteGroupItem;
                })
              );
            })
          ).pipe(
            map((resolvedSiteGroupItems) => ({
              ...data,
              items: resolvedSiteGroupItems,
            }))
          )
        : of(data);
    return dataProcessing$;
  }
}
