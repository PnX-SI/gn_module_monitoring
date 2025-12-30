import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { ConfigServiceG } from '../../services/config-g.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { CommonService } from '@geonature_common/service/common.service';
import { MediaService } from '@geonature_common/service/media.service';
import html2canvas from 'html2canvas';
import { MapService } from '@geonature_common/map/map.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { FormControl } from '@angular/forms';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';
import { TemplateData } from '../../interfaces/template';
import { PermissionService } from '../../services/permission.service';
import { FormService } from '../../services/form.service';

@Component({
  selector: 'pnx-monitoring-properties-g',
  templateUrl: './monitoring-properties-g.component.html',
  styleUrls: ['./monitoring-properties-g.component.css'],
})
export class MonitoringPropertiesGComponent implements OnInit {
  @Input() obj: any;
  @Input() objectType: string;
  @Input() currentUser;
  @Input() templateData: TemplateData;
  @Input() templateSpecific: TemplateData;
  @Input() bSynthese: boolean = false;

  public moduleCode: string = 'generic';
  public datasetForm: FormControl = new FormControl();
  public bUpdateSyntheseSpinner: boolean = false;
  public modalReference: any;
  public canUpdateObj: boolean;
  public selectedDataSet: Array<number> = [];
  public toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;
  public userPermission: any;

  constructor(
    private _configServiceG: ConfigServiceG,
    public ms: MediaService,
    private _dataService: DataMonitoringObjectService,
    private _commonService: CommonService,
    public ngbModal: NgbModal,
    public mapservice: MapService,
    public permissionService: PermissionService,
    private _formService: FormService
  ) {}

  ngOnInit() {
    this.moduleCode = this._configServiceG.moduleCode() ?? '';
    console.log(this.templateData.exportCSV, 'eeeee');
    // Si les permissions n'ont pas été initialisées
    this.userPermission =
      this.currentUser.moduleCruved ||
      this.permissionService.setModulePermissions(this._configServiceG.moduleCode() || 'generic');
  }

  hasEditPermission() {
    return this.userPermission[this.objectType]['U'] > 0;
  }

  onEditClick() {
    this._formService.changeCurrentEditMode(true);
  }

  updateSynthese() {
    this.bUpdateSyntheseSpinner = true;
    this._dataService.updateSynthese(this.moduleCode).subscribe(
      () => {
        this.bUpdateSyntheseSpinner = false;
        this._commonService.regularToaster(
          'success',
          `La synthèse a été mise à jour pour le module ${this.moduleCode}`
        );
      },
      (err) => {
        this.bUpdateSyntheseSpinner = false;
        this._commonService.regularToaster(
          'error',
          `Erreur lors de la mise à jour de la synthèse pour le module ${this.moduleCode} - ${err.error.message}`
        );
      }
    );
  }
  // add mje: show dowload modal
  openModalExportCsv(event, modal) {
    this.selectedDataSet = [];
    this.modalReference = this.ngbModal.open(modal, { size: 'lg' });
  }

  onDatasetChanged(id_dataset: any, i: number) {
    this.selectedDataSet[i] = id_dataset;
  }

  getExportCsv(exportDef: any, jd: number) {
    const queryParams = jd != null ? { id_dataset: jd } : {};
    console.log(exportDef);
    this._dataService.getExportCsv(this.moduleCode, exportDef.method, queryParams);
  }

  processExportPdf(exportPdfConfig: any) {
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
