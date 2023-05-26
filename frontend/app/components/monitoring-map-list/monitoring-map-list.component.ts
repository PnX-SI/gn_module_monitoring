import { Component,Input, OnInit, } from '@angular/core';
import { tap, mergeMap, map } from 'rxjs/operators';
import { SiteSiteGroup } from '../../interfaces/objObs';
import { MonitoringSitesComponent } from '../monitoring-sites/monitoring-sites.component';
import { FormService } from '../../services/form.service';
import { ApiGeomService } from '../../services/api-geom.service';
import { ConfigJsonService } from '../../services/config-json.service';
import { ObjectService } from '../../services/object.service';

@Component({
  selector: 'monitoring-map-list.component',
  templateUrl: './monitoring-map-list.component.html',
  styleUrls: ['./monitoring-map-list.component.css'],
})
export class MonitoringMapListComponent implements OnInit {
  
  // TODO: object needed to manage map 
  obj:any;
  bEdit:boolean = true;
  // 
  displayMap: boolean = true;
  siteSiteGroup: SiteSiteGroup | null = null;
  apiService: ApiGeomService;
  constructor( private _objService: ObjectService,private _formService: FormService,private _configService: ConfigJsonService) {}

  ngOnInit(){
        }
  initObj(prop) {
        // this.apiService.getConfig().subscribe(prop => this.obj['properties'] = prop)
        this.obj['properties'] = prop;
    }
  onActivate(component) {
    this.apiService = component['_sites_group_service']
    this._objService.currentObjectTypeParent
      .pipe(
        tap((data) => {
          console.log(data)
          this.obj = data;
          this.obj.bIsInitialized = true;
          this.obj.id = this.obj[this.obj.pk];
        }),
        mergeMap((data: any) => this._configService.init(data.moduleCode)),
        mergeMap(() => {
          return this.apiService.getConfig().pipe(
            map((prop) => {
              return {prop: prop };
            })
          );
        })
      )
      .subscribe((data) => {
        this.initObj(data.prop);
        this.obj.config = this._configService.configModuleObject(
          this.obj.moduleCode,
          this.obj.objectType
        );
        console.log(this.obj)
      })

  }
}
