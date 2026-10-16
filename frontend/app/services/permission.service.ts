import { Injectable } from '@angular/core';
import { TPermission } from '../types/permission';
import { ObjectPermission } from '../enum/objectPermission';
import { ConfigService as GnConfigService } from '@geonature/services/config.service';
import { ModuleService } from '@geonature/services/module.service';

@Injectable({
  providedIn: 'root', // a changer :/
})
export class PermissionService {
  modulePermission: TPermission;
  constructor(protected _moduleService: ModuleService) {}

  // Issue de ConfigService
  setModulePermissions(module_code: string) {
    if (module_code == 'generic') {
      module_code = 'MONITORINGS';
    }
    const module = this._moduleService.getModule(module_code);
    const moduleCruved: { [index: string]: any } = {};
    for (const [objectType, permObjectCode] of Object.entries(ObjectPermission)) {
      moduleCruved[objectType] =
        module.objects.find((o) => o.code_object == permObjectCode)?.cruved || module.cruved;
    }
    return moduleCruved;
  }

  setPermissionMonitorings(module_code: string = 'generic') {
    /**
     * Définition des permissions de l'utilisateur pour le module monitoring courrant
     *
     * Les permissions sont récupérées via le _moduleService
     *  qui récupère la liste des modules avec les permissions
     *  associées pour chaque type d'objets du module
     *
     *
     * @param {string} module_code - the code of the module
     *
     */

    if (module_code == 'generic') {
      module_code = 'MONITORINGS';
    }
    const moduleCruved = this.setModulePermissions(module_code);

    this.modulePermission = moduleCruved;
  }
}
