import { Component, Input, OnInit } from '@angular/core';
import { FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { SiteSiteGroup } from '../../interfaces/objObs';
import { ApiGeomService } from '../../services/api-geom.service';

@Component({
  selector: 'monitoring-map-list.component',
  templateUrl: './monitoring-map-list.component.html',
  styleUrls: ['./monitoring-map-list.component.css'],
})
export class MonitoringMapListComponent {
  // TODO: object needed to manage map
  obj: any;
  objForm: FormGroup;
  // Hauteur de la carte : hauteur du conteneur #object (voir CSS) moins ses marges
  heightMap: string = 'max(270px, calc(var(--gn-content-height) - 80px))';
  //
  displayMap: boolean = true;
  siteSiteGroup: SiteSiteGroup | null = null;
  apiService: ApiGeomService;
  moduleCode: string;

  constructor(
    private _Activatedroute: ActivatedRoute
  ) {}

  ngOnInit() {
    this.moduleCode = this._Activatedroute.snapshot.params.moduleCode;
  }

  onActivate() {}
}
