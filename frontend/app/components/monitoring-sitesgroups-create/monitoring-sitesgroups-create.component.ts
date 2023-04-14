import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { endPoints } from '../../enum/endpoints';
import { ISitesGroup } from '../../interfaces/geom';
import { FormService } from '../../services/form.service';

@Component({
  selector: 'monitoring-sitesgroups-create',
  templateUrl: './monitoring-sitesgroups-create.component.html',
  styleUrls: ['./monitoring-sitesgroups-create.component.css'],
})
export class MonitoringSitesGroupsCreateComponent implements OnInit {
  siteGroup: ISitesGroup;
  form: FormGroup;
  urlRelative: string;
  constructor(
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private route: ActivatedRoute
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
    this.form = this._formBuilder.group({});
  }
}
