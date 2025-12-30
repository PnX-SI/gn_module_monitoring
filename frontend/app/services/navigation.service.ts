import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import { ConfigService } from './config.service';
import { Router } from '@angular/router';
import { ConfigServiceG } from './config-g.service';

@Injectable()
export class NavigationService {
  constructor(
    private _configService: ConfigService,
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
    console.log('NavigationService.navigateToDetail()', this._configServiceG.config());
    this.navigate('object', moduleCode, objectType, id, {
      parents_path: parentsPath,
      edit: toEdit,
    });
  }

  navigateToParent(
    moduleCode: string,
    objectType: string,
    parentId: number | null,
    parentsPath = null
  ) {
    console.log(
      'NavigationService.navigateToParent()',
      objectType,
      parentsPath,
      parentId,
      moduleCode
    );
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
    console.log('NavigationService.navigate()');
    let editParams = '';
    if ('edit' in queryParams && queryParams.edit == true) {
      editParams = 'true';
      delete queryParams.edit;
    }
    console.log('this._router.navigate', [
      this._configService.frontendModuleMonitoringUrl(),
      routeType,
      moduleCode,
      objectType,
      id,
      { edit: editParams },
    ]);
    this._router.navigate(
      [
        this._configService.frontendModuleMonitoringUrl(),
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
        this._configService.frontendModuleMonitoringUrl(),
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
}
