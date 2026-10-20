import { Injectable } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivateChild,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { CommonService } from '@geonature_common/service/common.service';
import { PermissionService } from '../services/permission.service';

/**
 * Empêche l'accès aux vues d'un sous-module (page d'accueil, objets) si l'utilisateur n'a pas
 * le droit de lecture sur le sous-module (objet MONITORINGS_MODULES), comme la liste des modules
 * qui ne l'affiche pas. Redirection vers la liste des modules.
 */
@Injectable({ providedIn: 'root' })
export class ModulePermissionGuard implements CanActivateChild {
  constructor(
    private _permissionService: PermissionService,
    private _commonService: CommonService,
    private _router: Router
  ) {}

  canActivateChild(
    childRoute: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): boolean | UrlTree {
    // Seule la route finale est contrôlée
    if (childRoute.firstChild) {
      return true;
    }

    const moduleCode = childRoute.pathFromRoot.find((r) => r.params?.moduleCode)?.params.moduleCode;
    if (!moduleCode || moduleCode === 'generic') {
      return true;
    }

    let canRead = false;
    try {
      canRead = this._permissionService.setModulePermissions(moduleCode).module?.R > 0;
    } catch (e) {
      // module absent de la liste des modules accessibles à l'utilisateur
      canRead = false;
    }
    if (canRead) {
      return true;
    }
    this._commonService.regularToaster(
      'error',
      "Vous n'avez pas les permissions nécessaires pour accéder à ce module"
    );
    const baseUrl = state.url.split(`/object/${moduleCode}`)[0];
    return this._router.parseUrl(baseUrl);
  }
}
