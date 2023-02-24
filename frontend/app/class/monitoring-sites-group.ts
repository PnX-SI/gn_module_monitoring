export enum columnNameSiteGroup {
  sites_group_name = "Nom",
  nb_sites = "Nb. sites",
  nb_visits = "Nb. visites",
  sites_group_code = "Code",
}

export const extendedDetailsSiteGroup = {
  ...columnNameSiteGroup,
  comments: "Commentaires",
  sites_group_description: "Description",
};
