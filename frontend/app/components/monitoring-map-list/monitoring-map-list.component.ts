import { Component, Input, OnInit } from '@angular/core';
import { tap, mergeMap, map, distinctUntilChanged } from 'rxjs/operators';
import { SiteSiteGroup } from '../../interfaces/objObs';
import { FormService } from '../../services/form.service';
import { ApiGeomService } from '../../services/api-geom.service';
import { ConfigJsonService } from '../../services/config-json.service';
import { ObjectService } from '../../services/object.service';
import { CommonService } from '@geonature_common/service/common.service';
import { FormGroup } from '@angular/forms';

@Component({
  selector: 'monitoring-map-list.component',
  templateUrl: './monitoring-map-list.component.html',
  styleUrls: ['./monitoring-map-list.component.css'],
})
export class MonitoringMapListComponent {
  // TODO: object needed to manage map
  obj: any;
  bEdit: boolean;
  objForm: FormGroup;
  heightMap: string = '80vh';
  //
  displayMap: boolean = true;
  siteSiteGroup: SiteSiteGroup | null = null;
  apiService: ApiGeomService;

  constructor(
    private _formService: FormService,
    private _commonService: CommonService
  ) {}

  ngAfterViewInit() {
    const container = document.getElementById('object');
    const height = this._commonService.calcCardContentHeight();
    container.style.height = height - 40 + 'px';
    setTimeout(() => {
      this.heightMap = height - 80 + 'px';
    });
  }

  onActivate(component) {
    this._formService.currentFormMap
      .pipe(distinctUntilChanged((prev, curr) => prev.obj === curr.obj))
      .subscribe((formMapObj) => {
        this.obj = formMapObj.obj;
        this.bEdit = formMapObj.bEdit;
        this.objForm = formMapObj.frmGp;
      });
  }
}
