import { Injectable } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivateChild,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ConfigServiceG } from '../services/config-g.service';
import { MonitoringModuleDetailComponent } from '../components/monitoring-module-detail/monitoring-module-detail.component';

/**
 * Empêche l'accès aux vues des objets d'un module (création, modification, détail, listes)
 * tant que le module n'est pas configuré (liste d'observateurs et jeu(x) de données associés).
 *
 * Seule la page d'accueil du module (MonitoringModuleDetailComponent) reste accessible :
 * elle affiche un message invitant l'utilisateur à configurer le module.
 */
@Injectable({ providedIn: 'root' })
export class ModuleConfiguredGuard implements CanActivateChild {
  constructor(
    private _configServiceG: ConfigServiceG,
    private _router: Router
  ) {}

  canActivateChild(
    childRoute: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> | boolean {
    // Seule la route finale est contrôlée
    if (childRoute.firstChild || childRoute.component === MonitoringModuleDetailComponent) {
      return true;
    }

    const moduleCode = childRoute.pathFromRoot.find((r) => r.params?.moduleCode)?.params.moduleCode;
    if (!moduleCode || moduleCode === 'generic') {
      return true;
    }

    // Chargement de la config si nécessaire
    return this._configServiceG.init(moduleCode).pipe(
      map(() => {
        if (this._configServiceG.config()?.configured !== false) {
          return true;
        }
        // Redirection vers la page d'accueil du module
        const baseUrl = state.url.split(`/object/${moduleCode}`)[0];
        return this._router.parseUrl(`${baseUrl}/object/${moduleCode}/sites_group`);
      })
    );
  }
}
