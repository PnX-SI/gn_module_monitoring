import { ObjectsPermissionMonitorings } from '../enum/objectPermission';
import { IPermission } from '../interfaces/permission';

export type TPermission = Record<ObjectsPermissionMonitorings, IPermission>;
