const getElementSiteGroupBC = {
  description: 'Liste des groupes de site',
  label: '',
  url: 'object/generic/sites_group',
};

const getElementSiteBC = {
  description: 'Liste des sites',
  label: '',
  url: 'object/generic/site',
};

export class breadCrumbBase {
  static readonly baseBreadCrumbSiteGroups = new breadCrumbBase(
    'baseBreadCrumbSiteGroups',
    getElementSiteGroupBC
  );
  static readonly baseBreadCrumbSites = new breadCrumbBase('baseBreadCrumbSites', getElementSiteBC);
  // private to disallow creating other instances of this type
  private constructor(
    private readonly key: string,
    public readonly value: any
  ) {}

  toString() {
    return this.key;
  }
}
