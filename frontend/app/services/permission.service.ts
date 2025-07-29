import { Injectable } from '@angular/core';
import { TPermission } from '../types/permission';
import { ReplaySubject, BehaviorSubject } from 'rxjs';
import { ObjectsPermissionMonitorings as typePerm } from '../enum/objectPermission';
import { ConfigService as GnConfigService } from '@geonature/services/config.service';
import { ModuleService } from '@geonature/services/module.service';

@Injectable()
export class PermissionService {
  defaultPermission: TPermission = {
    [typePerm.MONITORINGS_GRP_SITES]: {
      canCreate: false,
      canRead: false,
      canUpdate: false,
      canDelete: false,
    },
    [typePerm.MONITORINGS_SITES]: {
      canCreate: false,
      canRead: false,
      canUpdate: false,
      canDelete: false,
    },
    [typePerm.MONITORINGS_INDIVIDUALS]: {
      canCreate: false,
      canRead: false,
      canUpdate: false,
      canDelete: false,
    },
  };

  constructor(
    public appConfig: GnConfigService,
    protected _moduleService: ModuleService
  ) {}

  // Utilité que ce soit un BehaviorSubject ???
  private permissionObject = new BehaviorSubject<TPermission>(this.defaultPermission);

  currentPermissionObj = this.permissionObject.asObservable();

  setPermissionUser(permUser: TPermission) {
    this.permissionObject.next(permUser);
  }

  getPermissionUser() {
    return this.permissionObject.getValue();
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

    const permObjectDict = this.appConfig.MONITORINGS.PERMISSION_LEVEL;
    const module = this._moduleService.getModule(module_code);
    const listObjectCruved = {};

    for (const [objectCode, permObjectCode] of Object.entries(permObjectDict)) {
      listObjectCruved[String(permObjectCode)] =
        module.objects.find((o) => o.code_object == permObjectDict[objectCode])?.cruved ||
        module.cruved;
    }

    Object.keys(this.defaultPermission).forEach((objKey) => {
      this.defaultPermission[objKey].canRead = false;
      this.defaultPermission[objKey].canCreate = false;
      this.defaultPermission[objKey].canDelete = false;
      this.defaultPermission[objKey].canUpdate = false;
      if (objKey in listObjectCruved) {
        Object.keys(listObjectCruved[objKey]).forEach((action) => {
          switch (action) {
            case 'C':
              this.defaultPermission[objKey].canCreate = listObjectCruved[objKey][action];
              break;
            case 'R':
              this.defaultPermission[objKey].canRead = listObjectCruved[objKey][action];
              break;
            case 'U':
              this.defaultPermission[objKey].canUpdate = listObjectCruved[objKey][action];
              break;
            case 'D':
              this.defaultPermission[objKey].canDelete = listObjectCruved[objKey][action];
              break;
            default:
              break;
          }
        });
      }
    });
    this.setPermissionUser(this.defaultPermission);
  }
}
