import { ObjectType } from '../enum/objecttype';

export function getImportProperties(objectType: ObjectType, properties: any) {
  if ('visit' == objectType) {
    return {
      uuid_base_site: properties['uuid_base_site'], // todo: is it useful ?
      uuid_base_visit: properties['uuid_base_visit'],
    };
  }
  if ('site' == objectType) {
    return {
      uuid_base_site: properties['uuid_base_site'],
    };
  }
  return {};
}
