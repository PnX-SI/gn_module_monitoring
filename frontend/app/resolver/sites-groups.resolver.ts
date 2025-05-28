import { Injectable } from '@angular/core';
import { SitesGroupService, SitesService } from '../services/api-geom.service';
import { Observable, forkJoin, of } from 'rxjs';
import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot,Router } from '@angular/router';
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

const LIMIT = 10;

@Injectable({ providedIn: 'root' })
export class SitesGroupsResolver
  implements
    Resolve<{
      sitesGroups: { data: IPaginated<ISitesGroup>; objConfig: IobjObs<ISitesGroup> };
      sites: { data: IPaginated<ISite>; objConfig: IobjObs<ISite> };
      route: string;
      moduleCode: string | null;
    }>
{
  currentPermission: TPermission;

  constructor(
    public service: SitesGroupService,
    public serviceSite: SitesService,
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
    route: string;
    moduleCode: string | null;
  }> {
    const moduleCode = route.params.moduleCode || 'generic';
    this.service.setModuleCode(`${moduleCode}`);
    this.serviceSite.setModuleCode(`${moduleCode}`);

    const $getPermissionMonitoring = this._dataMonitoringObjectService.getCruvedMonitoring();
    const $permissionUserObject = this._permissionService.currentPermissionObj;
    const $configSitesGroups = this.service.initConfig();
    const $configSites = this.serviceSite.initConfig();
    const resolvedData = $getPermissionMonitoring.pipe(
      map((listObjectCruved: Object) => {
        this._permissionService.setPermissionMonitorings(listObjectCruved);
      }),
      concatMap(() =>
        $permissionUserObject.pipe(
          map((permissionObject: TPermission) => (this.currentPermission = permissionObject)),
        )
      ),
      concatMap(() =>  this._configService.init(moduleCode)),
      concatMap(() =>
        forkJoin([$configSitesGroups, $configSites]).pipe(
          map((configs) => {
            if (!configs[0] && state.url.includes("/monitorings/object/") && state.url.includes("sites_group") ) {
              this.router.navigate(['monitorings', 'object', route.params.moduleCode, 'site']);
            }
            
            const configSchemaSiteGroup = configs[0] ? this._configJsonService.configModuleObject(
              configs[0].moduleCode,
              configs[0].objectType
            ) : null;

            const configSchemaSite = configs[1] ? this._configJsonService.configModuleObject(
              configs[1].moduleCode,
              configs[1].objectType
            ) : null;

            const sortSiteGroupInit = configSchemaSiteGroup ?
              'sorts' in configSchemaSiteGroup
                ? {
                    sort_dir: configSchemaSiteGroup.sorts[0].dir,
                    sort: configSchemaSiteGroup.sorts[0].prop,
                  }
                : {} : null;
            const sortSiteInit = configSchemaSite ?
              'sorts' in configSchemaSite
                ? { sort_dir: configSchemaSite.sorts[0].dir, sort: configSchemaSite.sorts[0].prop }
                : {} : null;

            const $getSiteGroups = sortSiteGroupInit ? this.currentPermission.MONITORINGS_GRP_SITES.canRead
              ? this.service.get(1, LIMIT, sortSiteGroupInit)
              : of({ items: [], count: 0, limit: 0, page: 1 }) : of(null);
            const $getSites = sortSiteInit ? this.currentPermission.MONITORINGS_SITES.canRead
              ? this.serviceSite.get(1, LIMIT, sortSiteInit)
              : of({ items: [], count: 0, limit: 0, page: 1 }) : of(null);
            
            return forkJoin([$getSiteGroups, $getSites]).pipe(
              mergeMap(([siteGroups, sites]) => {
                const specificConfigSite = configSchemaSite?.specific;
                const specificConfigSiteGroup = configSchemaSiteGroup?.specific;

                const siteGroupsProcessing$ = (siteGroups && siteGroups.items && siteGroups.items.length > 0 && specificConfigSiteGroup && Object.keys(specificConfigSiteGroup).length > 0)
                  ? forkJoin(
                      siteGroups.items.map(siteGroupItem => {
                        const propertyObservables = {};
                        for (const attribut_name of Object.keys(specificConfigSiteGroup)) {
                          if (siteGroupItem.hasOwnProperty(attribut_name)) {
                            propertyObservables[attribut_name] = resolveProperty(
                              this._objService,
                              this._cacheService,
                              this._configService,
                              moduleCode,
                              specificConfigSiteGroup[attribut_name],
                              siteGroupItem[attribut_name]
                            );
                          }
                        }
                        if (Object.keys(propertyObservables).length === 0) {
                          return of(siteGroupItem);
                        }
                        return forkJoin(propertyObservables).pipe(
                          map(resolvedProperties => {
                            const updatedSiteGroupItem = { ...siteGroupItem };
                            for (const attribut_name of Object.keys(resolvedProperties)) {
                              updatedSiteGroupItem[attribut_name] = resolvedProperties[attribut_name];
                            }
                            return updatedSiteGroupItem;
                          })
                        );
                      })
                    ).pipe(map(resolvedSiteGroupItems => ({ ...siteGroups, items: resolvedSiteGroupItems })))
                  : of(siteGroups);
                
                const sitesProcessing$ = (sites && sites.items && sites.items.length > 0 && specificConfigSite && Object.keys(specificConfigSite).length > 0) 
                  ? forkJoin(
                    sites.items.map(siteItem => {
                      const propertyObservables = {};
                      for (const attribut_name of Object.keys(specificConfigSite)) {
                    if (siteItem.hasOwnProperty(attribut_name)) {
                      propertyObservables[attribut_name] = resolveProperty(
                        this._objService,
                        this._cacheService,
                        this._configService,
                        moduleCode,
                        specificConfigSite[attribut_name],
                        siteItem[attribut_name]
                      );
                    }
                  }

                  if (Object.keys(propertyObservables).length === 0) {
                    return of(siteItem);
                  }

                  return forkJoin(propertyObservables).pipe(
                    map(resolvedProperties => {
                      const updatedSiteItem = { ...siteItem };
                      for (const attribut_name of Object.keys(resolvedProperties)) {
                        updatedSiteItem[attribut_name] = resolvedProperties[attribut_name];
                      }
                      return updatedSiteItem;
                    })
                  );
                    })
                ).pipe(map(resolvedSiteItems => ({ ...sites, items: resolvedSiteItems })))
                : of(sites);


                return forkJoin([siteGroupsProcessing$, sitesProcessing$]).pipe(
                  map(([processedSiteGroups, processedSites]) => {
                    return {
                      sitesGroups: { data: processedSiteGroups, objConfig: configs[0] },
                      sites: { data: processedSites, objConfig: configs[1] },
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
}
