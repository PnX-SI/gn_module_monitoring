import { Injectable } from '@angular/core';
import { Observable, forkJoin, of } from 'rxjs';

import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { ISite, ISitesGroup } from '../interfaces/geom';
import { IPaginated } from '../interfaces/page';
import { IobjObs } from '../interfaces/objObs';
import { concatMap, map, mergeMap, filter, takeWhile } from 'rxjs/operators';
import { PermissionService } from '../services/permission.service';
import { TPermission } from '../types/permission';
import { MonitoringObjectService } from '../services/monitoring-object.service';
import { CacheService } from '../services/cache.service';
import { ConfigService } from '../services/config.service';
import { IIndividual } from '../interfaces/individual';
import { ObjectService } from '../services/object.service';
import { SitesGroupService, SitesService, IndividualsService } from '../services/api-geom.service';

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
  resolvedData;
  constructor(
    public serviceSitesGroup: SitesGroupService,
    public serviceSite: SitesService,
    public serviceIndividual: IndividualsService,
    public _permissionService: PermissionService,
    private router: Router,
    private _objectService: ObjectService,
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

    this._permissionService.setPermissionMonitorings(moduleCode);
    this.currentPermission = this._permissionService.getPermissionUser();
    this._configService.currentModuleConfig = null;
    this._configService.init(moduleCode);

    this.resolvedData = this._configService.currentModuleConfigObs.pipe(
      filter((config) => config != null),
      takeWhile((config) => config.module.module_code == moduleCode), //Permet de  unsubscribe dès que le module est le bon
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
          module_permissions['sites_group'].R,
          this.serviceSitesGroup
        );

        const $getSites = this.buildObjectConfig(
          'site',
          module_permissions['site'].R,
          this.serviceSite
        );

        const $getIndividuals = this.buildObjectConfig(
          'individual',
          module_permissions['individual'].R,
          this.serviceIndividual
        );

        return forkJoin([$getSiteGroups, $getSites, $getIndividuals]).pipe(
          map(([processedSiteGroups, processedSites, processedIndividuals]) => {
            return {
              sitesGroups: {
                data: processedSiteGroups,
                objConfig: this.serviceSitesGroup.objectObs,
              },
              sites: { data: processedSites, objConfig: this.serviceSite.objectObs },
              individuals: {
                data: processedIndividuals,
                objConfig: this.serviceIndividual.objectObs,
              },
              route: route['_urlSegment'].segments[3].path,
              permission: this.currentPermission,
              tree: this.listChildObjectType,
              moduleCode,
            };
          })
        );
      }),
      mergeMap((result) => {
        return result;
      })
    );
    return this.resolvedData;
  }
  buildObjectConfig(object_type, permission, objectService) {
    let configSchemaObjetType = {
      sorts: [],
      specific: {},
    };
    const config = objectService.objectObs;
    let $getObjetTypes = of(null);

    if (this.listChildObjectType.includes(object_type) && config) {
      configSchemaObjetType = this._configService.configModuleObject(
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
