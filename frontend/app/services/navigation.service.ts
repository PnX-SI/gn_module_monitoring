import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

import { ConfigServiceG } from './config-g.service';

@Injectable()
export class NavigationService {
  constructor(
    private _configServiceG: ConfigServiceG,
    private _router: Router
  ) {}

  navigateToAddChildren(
    id = null,
    siteId = null,
    moduleCode: string,
    objectType: string,
    childrenType: string,
    parentsPath = null
  ) {
    const queryParamsAddChildren = {};
    const idFielName = this._configServiceG.config()?.[objectType]['id_field_name'];
    queryParamsAddChildren[idFielName] = id;
    queryParamsAddChildren['siteId'] = siteId;
    queryParamsAddChildren['parents_path'] = (parentsPath || []).concat(objectType);

    if (moduleCode == 'generic') {
      this.navigateGeneric(
        'object',
        moduleCode,
        childrenType,
        null,
        'create',
        queryParamsAddChildren
      );
    } else {
      this.navigate('create_object', moduleCode, childrenType, null, queryParamsAddChildren);
    }
  }

  navigateToDetail(
    id: number,
    toEdit = false,
    moduleCode: string,
    objectType: string,
    parentsPath = null
  ) {
    this.navigate('object', moduleCode, objectType, id, {
      parents_path: parentsPath,
      edit: toEdit,
    });
  }

  navigateToParent(
    moduleCode: string,
    objectType: string,
    parentId: number | null,
    parentsPath: any[] | null = null
  ) {
    // cas module il n'y a pas de parent
    if (objectType.includes('module')) {
      this.navigateToDetail(null, false, moduleCode, 'module', []);
      // autres cas
    } else {
      const parentType = (parentsPath || []).pop() || 'module';
      let parentRouteType = parentType;
      // si le parent est un module on met null en id et on change le type de route
      if (parentType === 'module') {
        parentId = null;
        parentRouteType = objectType;
      }
      this.navigate('object', moduleCode, parentRouteType, parentId, {
        parents_path: parentsPath,
      });
    }
  }

  navigate(
    routeType: string,
    moduleCode: string,
    objectType: string,
    id: number,
    queryParams = {}
  ) {
    let editParams = '';
    if ('edit' in queryParams && queryParams.edit == true) {
      editParams = 'true';
      delete queryParams.edit;
    }
    this._router.navigate(
      [
        this._configServiceG.frontendModuleMonitoringUrl(),
        routeType,
        moduleCode,
        objectType,
        id,
        { edit: editParams },
      ].filter((s) => !!s),
      {
        queryParams,
      }
    );
  }

  navigateGeneric(routeType, moduleCode, objectType, id, action, queryParams = {}) {
    let editParams = '';
    if ('edit' in queryParams && queryParams.edit == true) {
      editParams = 'true';
      delete queryParams.edit;
    }

    this._router.navigate(
      [
        this._configServiceG.frontendModuleMonitoringUrl(),
        routeType,
        moduleCode,
        objectType,
        action,
        id,
        { edit: editParams },
      ].filter((s) => !!s),
      {
        queryParams,
      }
    );
  }

  /**
   * Recharge complètement la page d'accueil d'un module
   *
   * Les composants de la page d'accueil sont réutilisés par le router lors d'une navigation
   * vers la même route : ils ne prendraient pas en compte une nouvelle configuration du module.
   * On passe donc par la racine du module (sans modifier l'url du navigateur) pour forcer
   * leur recréation et la ré-exécution des resolvers.
   */
  reloadModuleHome(moduleCode: string) {
    const moduleUrl = this._configServiceG.frontendModuleMonitoringUrl();
    this._router
      .navigate([moduleUrl], { skipLocationChange: true })
      .then(() => this._router.navigate([moduleUrl, 'object', moduleCode, 'sites_group']));
  }
}
