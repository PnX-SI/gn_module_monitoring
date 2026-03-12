export function getImportProperties(obj: any) {
  const objectType = obj?.objectType;
  const properties = obj?.properties;
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
