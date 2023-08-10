import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';

import { endPoints } from '../../enum/endpoints';
import { ISitesGroup } from '../../interfaces/geom';
import { FormService } from '../../services/form.service';
import { SitesGroupService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { GeoJSONService } from '../../services/geojson.service';

@Component({
  selector: 'monitoring-sitesgroups-create',
  templateUrl: './monitoring-sitesgroups-create.component.html',
  styleUrls: ['./monitoring-sitesgroups-create.component.css'],
})
export class MonitoringSitesGroupsCreateComponent implements OnInit {
  siteGroup: ISitesGroup;
  objForm: FormGroup;
  urlRelative: string;
  constructor(
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public sitesGroupService: SitesGroupService,
    public geojsonService: GeoJSONService
  ) {}

  ngOnInit() {
    // Remove "create" segmentUrl
    this.urlRelative = '/monitorings';
    this._formService.dataToCreate(
      {
        module: 'generic',
        objectType: 'sites_group',
        id: null,
        endPoint: endPoints.sites_groups,
        objSelected: {},
      },
      this.urlRelative
    );
    this._objService.changeSelectedObj({}, true);
    this.objForm = this._formBuilder.group({});
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
  }
}
