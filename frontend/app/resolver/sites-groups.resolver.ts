import { Injectable } from '@angular/core';
import { SitesGroupService, SitesService, IndividualsService } from '../services/api-geom.service';
import { Observable, forkJoin, of } from 'rxjs';
import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { ISite, ISitesGroup } from '../interfaces/geom';
import { IPaginated } from '../interfaces/page';
import { IobjObs } from '../interfaces/objObs';
import { concatMap, map, mergeMap } from 'rxjs/operators';
import { PermissionService } from '../services/permission.service';
import { TPermission } from '../types/permission';
import { MonitoringObjectService } from '../services/monitoring-object.service';
import { CacheService } from '../services/cache.service';
import { ConfigService } from '../services/config.service';
import { IIndividual } from '../interfaces/individual';
import { ObjectService } from '../services/object.service';
import { ConfigServiceG } from '../services/config-g.service';

const LIMIT = 10;

@Injectable({ providedIn: 'root' })
export class SitesGroupsResolver
  implements
    Resolve<{
      sites_groups: IPaginated<ISitesGroup>;
      sites: IPaginated<ISite>;
      individuals: IPaginated<IIndividual>;
      route: string;
      moduleCode: string | null;
    }>
{
  // Liste des type d'objets enfants à afficher sur la page
  listChildObjectType: string[] = ['sites_group', 'site'];

  constructor(
    public serviceSitesGroup: SitesGroupService,
    public serviceSite: SitesService,
    public serviceIndividual: IndividualsService,
    public _permissionService: PermissionService,
    private router: Router,
    private _objectService: ObjectService,
    private _cacheService: CacheService,
    private _configService: ConfigService,
    private _configServiceG: ConfigServiceG
  ) {}

  resolve(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<{
    sites_groups: IPaginated<ISitesGroup>;
    sites: IPaginated<ISite>;
    individuals: IPaginated<IIndividual>;
    route: string;
    moduleCode: string | null;
  }> {
    const moduleCode = route.params.moduleCode || 'generic';
    this.listChildObjectType = ['sites_group', 'site'];

    this._permissionService.setPermissionMonitorings(moduleCode);
    const currentPermission = this._permissionService.modulePermission;

    this.serviceSitesGroup.initConfig();
    this.serviceSite.initConfig();
    this.serviceIndividual.initConfig();
    const tree = this._configServiceG.config()['tree'];

    // Si le module n'est pas le module générique affichage des objets
    // en fonction de l'objet tree
    if (moduleCode !== 'generic') {
      this.listChildObjectType = Object.keys(tree['module']);
    }

    // S'il n'y a pas de groupe de site  et que la page demandée est sites_group
    // redirection vers la page des sites.
    // TODO le rendre plus robuste
    if (
      !this.listChildObjectType.includes('sites_group') &&
      state.url.includes('/monitorings/object/') &&
      state.url.includes('sites_group')
    ) {
      this.router.navigate(['monitorings', 'object', route.params.moduleCode, 'site']);
    }

    // Initialisation des getters et config de chaque type d'objet
    const $getSiteGroups = this.buildObjectConfig(
      'sites_group',
      currentPermission.sites_group.R > 0,
      this.serviceSitesGroup
    );

    const $getSites = this.buildObjectConfig(
      'site',
      currentPermission.site.R > 0,
      this.serviceSite
    );

    const $getIndividuals = this.buildObjectConfig(
      'individual',
      currentPermission.individual.R > 0,
      this.serviceIndividual
    );

    return forkJoin([$getSiteGroups, $getSites, $getIndividuals]).pipe(
      map(([processedSiteGroups, processedSites, processedIndividuals]) => {
        // La configuration des objets enfants est renvoyée uniquement si l'objet est dans la liste des objets à afficher
        // TODO ne pas récupérer les données et la config si l'objet n'est pas dans la liste des objets à afficher
        return {
          sites_groups: processedSiteGroups,
          sites: processedSites,
          individuals: processedIndividuals,
          route: route['_urlSegment'].segments[3].path,
          permission: currentPermission,
          moduleCode,
        };
      })
    );
  }

  buildObjectConfig(object_type, permission, objectService) {
    const config = this._configServiceG.config();
    let $getObjetTypes = of(null);
    if (this.listChildObjectType.includes(object_type) && config) {
      const configSchemaObjetType = config[object_type];
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
