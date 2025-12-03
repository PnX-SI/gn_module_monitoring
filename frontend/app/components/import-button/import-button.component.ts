import { distinctUntilChanged } from 'rxjs/operators';
import { Component, OnInit, Input, Output, SimpleChanges, EventEmitter } from '@angular/core';
import { CruvedStoreService } from '@geonature_common/service/cruved-store.service';

@Component({
  selector: 'pnx-monitoring-import-button',
  templateUrl: 'import-button.component.html',
  styleUrls: ['./import-button.component.css'],
})
export class ImportButtonComponent implements OnInit {
  public canImport: boolean = false;
  @Input() moduleCode: string = 'generic';
  @Input() objectType: any = {};
  @Input() properties: any = {};

  constructor(public _cruvedStore: CruvedStoreService) {}

  ngOnInit() {
    console.log(this.objectType, this.properties);
    const userCruved =
      this._cruvedStore.cruved[this.moduleCode].module_objects.MONITORINGS_SITES.cruved;

    let cruvedImport: any = {};
    if (this._cruvedStore.cruved.IMPORT) {
      cruvedImport = this._cruvedStore.cruved.IMPORT.module_objects.IMPORT.cruved;
    }
    this.canImport = cruvedImport.C > 0 && userCruved.C > 0;
  }

  get importRoute(): string {
    return `/import/${this.moduleCode}/process/upload`;
  }

  getImportQueryParams() {
    if ('visit' == this.objectType) {
      return {
        uuid_base_site: this.properties['uuid_base_site'], // todo: is it useful ?
        uuid_base_visit: this.properties['uuid_base_visit'],
      };
    }
    if ('site' == this.objectType) {
      return {
        uuid_base_site: this.properties['uuid_base_site'],
      };
    }
    return {};
  }
}
