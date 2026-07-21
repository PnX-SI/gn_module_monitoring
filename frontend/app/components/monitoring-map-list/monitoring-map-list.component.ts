import { Component, Input, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { tap, mergeMap, map, distinctUntilChanged } from 'rxjs/operators';
import { SiteSiteGroup } from '../../interfaces/objObs';
import { FormService } from '../../services/form.service';
import { ApiGeomService } from '../../services/api-geom.service';
import { CommonService } from '@geonature_common/service/common.service';
import { FormGroup } from '@angular/forms';
import { Router, NavigationStart, ActivatedRoute } from '@angular/router';

@Component({
  selector: 'monitoring-map-list.component',
  templateUrl: './monitoring-map-list.component.html',
  styleUrls: ['./monitoring-map-list.component.css'],
})
export class MonitoringMapListComponent {
  // TODO: object needed to manage map
  obj: any;
  bEdit$: Observable<Boolean> = this._formService.currentEditMode;
  objForm: FormGroup;
  heightMap: string = '80vh';
  //
  displayMap: boolean = true;
  siteSiteGroup: SiteSiteGroup | null = null;
  apiService: ApiGeomService;
  moduleCode: string;

  constructor(
    private _formService: FormService,
    private _commonService: CommonService,
    private _router: Router,
    private _Activatedroute: ActivatedRoute
  ) {}

  ngOnInit() {
    this.moduleCode = this._Activatedroute.snapshot.params.moduleCode;
  }

  ngAfterViewInit() {
    const container = document.getElementById('object');
    const height = this._commonService.calcCardContentHeight();
    container.style.height = height - 40 + 'px';
    setTimeout(() => {
      this.heightMap = height - 80 + 'px';
    });
  }

  onActivate() {}
}
