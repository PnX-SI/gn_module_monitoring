import { Observable } from "rxjs/Observable";
import "rxjs/add/observable/of";

import { Component, OnInit } from '@angular/core';
import { MonitoringObject } from '../../class/monitoring-object';

import { ConfigService } from "../../services/config.service";
import { MonitoringObjectService } from "../../services/monitoring-object.service";
import { ActivatedRoute, Router } from "@angular/router";

import { dataTest } from './data_test'

@Component({
  selector: 'test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css']
})
export class TestComponent implements OnInit {

  msg = [];

  constructor(
    private _route: ActivatedRoute,
    private _configService: ConfigService,
    private _objService: MonitoringObjectService,
  ) { }

  public module:  MonitoringObject;
  public site:  MonitoringObject;
  public visit:  MonitoringObject;
  public observation:  MonitoringObject;


  ngOnInit() {
    this._route.paramMap
      .flatMap((params) => {
        return Observable.of(true);
      })
      .flatMap(() => {
        return this._configService.init('test');
      })
      .subscribe(()=>{
        this.log('info', 'init config');
      });
  }

  onClickAll() {
    this.test_all().subscribe(() => (
      this.log('info', 'tests effectués')
    ));
  }

  log(typeMsg, msg) {
    this.msg.push({ 'key': typeMsg, 'text': msg });
    console.log(`Msg - ${typeMsg} : ${msg}`);
  }


  test_post() {
    this.log('info', 'post module');
    this.module = new MonitoringObject('test', 'module', null, this._objService);
    return this.module.post(dataTest['module'])
      .flatMap(() => {
        this.site = new MonitoringObject(this.module.modulePath, 'site', null, this._objService);
        this.site.parentId = this.module.id;
        return this.site.post(dataTest['site']);
      })
      .flatMap(() => {
        this.visit = new MonitoringObject(this.module.modulePath, 'visit', null, this._objService);
        this.visit.parentId = this.visit.id;
        dataTest['visit']['id_base_site'] = this.site.id;
        return this.visit.post(dataTest['visit']);
      })
      .flatMap(() => {
        this.observation = new MonitoringObject(this.module.modulePath, 'observation', null, this._objService);
        this.observation.parentId = this.observation.id;
        dataTest['observation']['id_base_visit'] = this.visit.id;
        return this.observation.post(dataTest['observation']);
      });
  }

  test_patch() {
    this.log('info', 'patch module');
    return this.module.patch(dataTest['module'])
    .flatMap(() => {
      this.log('info', 'patch site');
      return this.site.patch(dataTest['site']);
    })
    .flatMap(() => {
      this.log('info', 'patch visit');
      return this.visit.patch(dataTest['visit']);
    })
    .flatMap(() => {
      this.log('info', 'patch observation');
      return this.observation.patch(dataTest['observation']);
    });

  }

  test_get() {
    this.log('info', 'get module');
    return this.module.get(true)
    .flatMap(() => {
      this.log('info', 'get site');
      return this.site.get(true);
    })
    .flatMap(() => {
      this.log('info', 'get visit');
      return this.visit.get(true);
    })
    .flatMap(() => {
      this.log('info', 'get observation');
      return this.observation.get(true);
    });
  }

  test_delete() {
    return Observable.of(true)
    .flatMap(() => {
      this.log('info', 'delete observation');
      return this.observation.delete();
    })
    .flatMap(() => {
      this.log('info', 'delete visit');
      return this.visit.delete();
    })
    .flatMap(() => {
      this.log('info', 'delete site');
      return this.site.delete();
    })
    .flatMap(() => {
      this.log('info', 'delete module');
      return this.module.delete();
    });
  }

  test_all() {
    return this.test_post()
      .flatMap(() => {return this.test_patch()})
      .flatMap(() => {return this.test_get()})
      .flatMap(() => {return this.test_delete()})
  }

}
