import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { MonitoringObject } from '../../class/monitoring-object';
import { ConfigService } from '../../services/config.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { CommonService } from '@geonature_common/service/common.service';
import { MediaService } from '@geonature_common/service/media.service';
import html2canvas from 'html2canvas';
import { MapService } from "@geonature_common/map/map.service";
import { NgbModal } from "@ng-bootstrap/ng-bootstrap";
import { FormGroup, FormBuilder, Validators } from "@angular/forms";


@Component({
  selector: 'pnx-monitoring-properties',
  templateUrl: './monitoring-properties.component.html',
  styleUrls: ['./monitoring-properties.component.css']
})
export class MonitoringPropertiesComponent implements OnInit {

  @Input() obj: MonitoringObject;
  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  @Input() currentUser;


  datasetForm: FormGroup;
  datasetFormDef = [];
  backendUrl: string;
  bUpdateSyntheseSpinner = false;

  public modalReference;
  selectedDataSet=null;

  constructor(
    private _configService: ConfigService,
    public ms: MediaService,
    private _dataService: DataMonitoringObjectService,
    private _commonService: CommonService,
    public ngbModal: NgbModal,
    public mapservice: MapService,
  ) {}

  ngOnInit() {
    this.backendUrl = this._configService.backendUrl();
    this.setDatasetFormDef();

  }

  setDatasetFormDef() {
    this.datasetFormDef = [
      {
          "attribut_name": "id_dataset",
          "type_widget": "datalist",
          "attribut_label": "Choisir un jeu de données à télécharger",
          "type_util": "dataset",
          "api": "meta/datasets",
          "application": "GeoNature",
          "keyValue": "id_dataset",
          "keyLabel": "dataset_shortname",
          "params": {
            "orderby": "dataset_name",
            "module_code": this.obj.moduleCode
          },
          "required": true
        },
    ];
  }

  onEditClick() {
    this.bEditChange.emit(true);
  }

  updateSynthese() {
    this.bUpdateSyntheseSpinner = true;
    this._dataService.updateSynthese(this.obj.moduleCode).subscribe(
      () => {
        this.bUpdateSyntheseSpinner = false;
        this._commonService.regularToaster('success', `La syntèse à été mise à jour pour le module ${this.obj.moduleCode}`);
      },
      (err) => {
        this.bUpdateSyntheseSpinner = false;
        this._commonService.regularToaster('error', `Erreur lors de la mise à jour de la syntèse pour le module ${this.obj.moduleCode} - ${err.error.message}`);
      }
    );
  }
  // add mje: show dowload modal
  openModalExportCsv(event, modal) {
    this.modalReference = this.ngbModal.open(modal, { size: "lg" });
  }

  onDatasetChanged(event: any) {
    //update the ui
    console.log(event)
    this.selectedDataSet = event.id_dataset;
  }

   getExportCsv(type,method,jd) {
     console.log(jd)
    this._dataService.getExportCsv(this.obj.moduleCode,type,method,jd);
  }

      //mje: generate PDF export
  processExportPdf(exportPdfConfig) {

    var map=this.mapservice.map;
    const $this=this;

    try {
      var zoomInElement = document.querySelector('#monitoring-map-container .leaflet-control-zoom-in');
      var snapshotElement=document.getElementById("geometry");
      var config= {
          allowTaint:true,
          useCORS: true  ,
          ignoreElements: function (element) {
              return element.classList[0] =='leaflet-control-zoom-in'
                  || element.classList[0] =='leaflet-control-zoom-out'
                  || element.classList[0] == 'leaflet-control-layers-toggle'
                  || element.title=='A JS library for interactive maps'
                  || element.placeholder=='Rechercher un lieu'
          },
          logging: false
        }

      html2canvas(snapshotElement,config).then(function(canvas) {
        var imgData = canvas.toDataURL("image/png");
        const extra_data = {
          resolved_properties: $this.obj.resolvedProperties
        }
        $this._dataService
          .postPdfExport(
            $this.obj.moduleCode,
            $this.obj.objectType,
            $this.obj.id,
            exportPdfConfig.template,
            imgData,
            extra_data
          ).subscribe(() => {
            $this._commonService.regularToaster(
              "success",
              "L'export pdf est prêt à être récupéré dans le dossier de Téléchargement"
            );
          });
      });

    } catch{
      $this._commonService.regularToaster(
        "error",
        "Une erreur est survenue durant l'export pdf"
      );
    }

  }



}
