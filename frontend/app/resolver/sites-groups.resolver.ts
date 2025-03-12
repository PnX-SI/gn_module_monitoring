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
    private router: Router
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
              map(([siteGroups, sites]) => {
                return {
                  sitesGroups: { data: siteGroups, objConfig: configs[0] },
                  sites: { data: sites, objConfig: configs[1] },
                  route: route['_urlSegment'].segments[3].path,
                  permission: this.currentPermission,
                  moduleCode,
                };
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
