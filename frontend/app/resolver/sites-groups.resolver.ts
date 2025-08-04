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
import { MonitoringObjectService } from '../services/monitoring-object.service';
import { CacheService } from '../services/cache.service';
import { ConfigService } from '../services/config.service';
import { IIndividual } from '../interfaces/individual';

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
  // Liste des type d'objets enfants à afficher sur la page
  listChildObjectType: string[] = ['sites_group', 'site'];

  constructor(
    public serviceSitesGroup: SitesGroupService,
    public serviceSite: SitesService,
    public serviceIndividual: IndividualsService,
    public _configJsonService: ConfigJsonService,
    public _permissionService: PermissionService,
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
    this.listChildObjectType = ['sites_group', 'site'];
    this.serviceSitesGroup.setModuleCode(`${moduleCode}`);
    this.serviceSite.setModuleCode(`${moduleCode}`);
    this.serviceIndividual.setModuleCode(`${moduleCode}`);

    const $configSitesGroups = this.serviceSitesGroup.initConfig();
    const $configSites = this.serviceSite.initConfig();
    const $configIndividuals = this.serviceIndividual.initConfig();

    this._permissionService.setPermissionMonitorings(moduleCode);
    this.currentPermission = this._permissionService.getPermissionUser();

    const resolvedData = this._configService.init(moduleCode).pipe(
      concatMap(() =>
        forkJoin([$configSitesGroups, $configSites, $configIndividuals]).pipe(
          map((configs) => {
            // Récupération des permissions du module
            const module_permissions = this._configService.moduleCruved(moduleCode);

            // Si le module n'est pas le module générique affichage des objets
            // en fonction de l'objet tree
            if (moduleCode !== 'generic') {
              const tree = this._configService.configModuleObject(moduleCode, 'tree');
              this.listChildObjectType = Object.keys(tree['module']);
            }

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
            const $getSiteGroups = this.buildObjectConfig(
              'sites_group',
              configs[0],
              module_permissions['sites_group'].R,
              this.serviceSitesGroup,
              moduleCode
            );

            const $getSites = this.buildObjectConfig(
              'site',
              configs[1],
              module_permissions['site'].R,
              this.serviceSite,
              moduleCode
            );

            const $getIndividuals = this.buildObjectConfig(
              'individual',
              configs[2],
              module_permissions['individual'].R,
              this.serviceIndividual,
              moduleCode
            );

            return forkJoin([$getSiteGroups, $getSites, $getIndividuals]).pipe(
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
          }),
          mergeMap((result) => {
            return result;
          })
        )
      )
    );
    return resolvedData;
  }

  buildObjectConfig(object_type, config, permission, objectService, moduleCode) {
    let configSchemaObjetType = {
      sorts: [],
      specific: {},
    };
    let $getObjetTypes = of(null);
    if (this.listChildObjectType.includes(object_type) && config) {
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
          ? objectService.getResolved(1, LIMIT, sortObjetTypeInit)
          : of({ items: [], count: 0, limit: 0, page: 1 });
    }
    return $getObjetTypes;
  }
}
