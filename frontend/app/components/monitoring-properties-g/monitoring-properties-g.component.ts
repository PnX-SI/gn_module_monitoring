import { Component, EventEmitter, Input, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Subscription } from 'rxjs';

import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { ISitesGroup } from '../../interfaces/geom';
import { IobjObs, ObjDataType } from '../../interfaces/objObs';
import { FormService } from '../../services/form.service';
import { JsonData } from '../../types/jsondata';
import { TPermission } from '../../types/permission';
import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { MonitoringObject } from '../../class/monitoring-object';
import { ConfigService } from '../../services/config.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { CommonService } from '@geonature_common/service/common.service';
import { MediaService } from '@geonature_common/service/media.service';
import html2canvas from 'html2canvas';
import { MapService } from '@geonature_common/map/map.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { FormGroup, FormControl, FormBuilder, Validators } from '@angular/forms';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { TemplateData } from '../../interfaces/template';

@Component({
  selector: 'pnx-monitoring-properties-g',
  templateUrl: './monitoring-properties-g.component.html',
  styleUrls: ['./monitoring-properties-g.component.css'],
})
export class MonitoringPropertiesGComponent implements OnInit {
  @Input() obj: any;
  @Input() templateData: TemplateData;
  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() currentUser;
  moduleCode:string="generic"
  @Input() objectType:string;
;
  datasetForm = new FormControl();
  backendUrl: string;
  bUpdateSyntheseSpinner = false;

  public modalReference;
  selectedDataSet: Array<number> = [];

  canUpdateObj: boolean;

  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;

  @Input() templateSpecific: any = {};

  constructor(
    private _configService: ConfigService,
    private _configServiceG: ConfigServiceG,
    public ms: MediaService,
    private _dataService: DataMonitoringObjectService,
    private _commonService: CommonService,
    public ngbModal: NgbModal,
    public mapservice: MapService
  ) {}

  ngOnInit() {
    this.moduleCode = this._configServiceG.moduleCode() ?? ""
    // Si les permissions n'ont pas été initialisées
    if (this.currentUser.moduleCruved == undefined) {
      this.currentUser.moduleCruved = this._configService.moduleCruved(this.moduleCode);
      
    }
    console.log(this.templateData,"templateData")
    console.log(this.templateSpecific,"templateDataS")
  }

  initPermission() {
    this.canUpdateObj =
      this.obj.objectType == 'module'
        ? this.currentUser?.moduleCruved[this.obj.objectType]['U'] > 0
        : this.obj?.cruved?.U;
    return this.canUpdateObj;
  }

  onEditClick() {
    this.bEditChange.emit(true);
  }

  updateSynthese() {
    this.bUpdateSyntheseSpinner = true;
    this._dataService.updateSynthese(this.moduleCode).subscribe(
      () => {
        this.bUpdateSyntheseSpinner = false;
        this._commonService.regularToaster(
          'success',
          `La synthèse a été mise à jour pour le module ${this.obj.moduleCode}`
        );
      },
      (err) => {
        this.bUpdateSyntheseSpinner = false;
        this._commonService.regularToaster(
          'error',
          `Erreur lors de la mise à jour de la synthèse pour le module ${this.obj.moduleCode} - ${err.error.message}`
        );
      }
    );
  }
  // add mje: show dowload modal
  openModalExportCsv(event, modal) {
    this.selectedDataSet = [];
    this.modalReference = this.ngbModal.open(modal, { size: 'lg' });
  }

  onDatasetChanged(id_dataset: any, i) {
    //update the ui
    this.selectedDataSet[i] = id_dataset;
  }

  getExportCsv(exportDef: any, jd: number) {
    const queryParams = jd != null ? { id_dataset: jd } : {};
    this._dataService.getExportCsv(this.obj.moduleCode, exportDef.method, queryParams);
  }

  //mje: generate PDF export
  processExportPdf(exportPdfConfig) {
    var map = this.mapservice.map;
    const $this = this;

    try {
      var zoomInElement = document.querySelector(
        '#monitoring-map-container .leaflet-control-zoom-in'
      );
      var snapshotElement = document.getElementById('geometry');
      var config = {
        allowTaint: true,
        useCORS: true,
        ignoreElements: function (element) {
          return (
            element.classList[0] == 'leaflet-control-zoom-in' ||
            element.classList[0] == 'leaflet-control-zoom-out' ||
            element.classList[0] == 'leaflet-control-layers-toggle' ||
            element.title == 'A JS library for interactive maps' ||
            element.placeholder == 'Rechercher un lieu'
          );
        },
        logging: false,
      };

      html2canvas(snapshotElement, config).then(function (canvas) {
        var imgData = canvas.toDataURL('image/png');
        const extra_data = {
          resolved_properties: $this.obj.resolvedProperties,
        };
        $this._dataService
          .postPdfExport(
            $this.obj.moduleCode,
            $this.obj.objectType,
            $this.obj.id,
            exportPdfConfig.template,
            imgData,
            extra_data
          )
          .subscribe(() => {
            $this._commonService.regularToaster(
              'success',
              "L'export PDF est prêt à être récupéré dans le dossier de Téléchargement"
            );
          });
      });
    } catch {
      $this._commonService.regularToaster('error', "Une erreur est survenue durant l'export PDF");
    }
  }
}
