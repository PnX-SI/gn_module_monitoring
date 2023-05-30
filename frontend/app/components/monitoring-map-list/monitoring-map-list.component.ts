import { Component,Input, OnInit, } from '@angular/core';
import { tap, mergeMap, map } from 'rxjs/operators';
import { SiteSiteGroup } from '../../interfaces/objObs';
import { MonitoringSitesComponent } from '../monitoring-sites/monitoring-sites.component';
import { FormService } from '../../services/form.service';
import { ApiGeomService } from '../../services/api-geom.service';
import { ConfigJsonService } from '../../services/config-json.service';
import { ObjectService } from '../../services/object.service';
import { FormGroup } from "@angular/forms";
@Component({
  selector: 'monitoring-map-list.component',
  templateUrl: './monitoring-map-list.component.html',
  styleUrls: ['./monitoring-map-list.component.css'],
})
export class MonitoringMapListComponent {
  
  // TODO: object needed to manage map 
  obj:any;
  bEdit: boolean;
  objForm: FormGroup;
  // 
  displayMap: boolean = true;
  siteSiteGroup: SiteSiteGroup | null = null;
  apiService: ApiGeomService;
  constructor( private _objService: ObjectService,private _formService: FormService,private _configService: ConfigJsonService) {}

  initObj(prop) {
        // this.apiService.getConfig().subscribe(prop => this.obj['properties'] = prop)
        this.obj['properties'] = prop;
    }
  onActivate(component) {
    this._formService.currentFormMap.subscribe(formMapObj => {
      this.obj = formMapObj.objForm
      this.bEdit = formMapObj.bEdit
      this.objForm = formMapObj.frmGp
    })

  }
}
