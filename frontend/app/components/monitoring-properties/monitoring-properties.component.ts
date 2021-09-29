import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { MonitoringObject } from '../../class/monitoring-object';
import { ConfigService } from '../../services/config.service';
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { CommonService } from '@geonature_common/service/common.service';
import { MediaService } from '@geonature_common/service/media.service';
import html2canvas from 'html2canvas';
import { MapService } from "@geonature_common/map/map.service";
import { NgbModal } from "@ng-bootstrap/ng-bootstrap";


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

  backendUrl: string;
  bUpdateSyntheseSpinner = false;

  public modalReference;
  selectedDataSet: string = '';

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
  openModalDownload(event, modal) {
    this.modalReference = this.ngbModal.open(modal, { size: "lg" });
  }
  selectChangeHandler (event: any) {
    //update the ui
    this.selectedDataSet = event.target.value;
  }

   downloadAllObservations(type,method,jd) {
    this._dataService.downloadAllObservations(this.obj.moduleCode,type,method,jd);
  }

      //mje: generate PDF export
getMapArea() {
  var map=this.mapservice.map;
  const me=this;

//-------------------------
//var code_commune=(this.obj.resolvedProperties['commune'][0]);
//var commune=this._dataService.getCommune(code_commune);

   try{
    var zoomInElement = document.querySelector('#monitoring-map-container .leaflet-control-zoom-in');
    var snapshotelement=document.getElementById("geometry"); 
    var config= {
        allowTaint:true,
        useCORS: true  ,
        ignoreElements: function (element) {
            if ( element.classList[0] =='leaflet-control-zoom-in' || element.classList[0] =='leaflet-control-zoom-out' || element.classList[0] == 'leaflet-control-layers-toggle' ||element.title=='A JS library for interactive maps' || element.placeholder=='Rechercher un lieu')  {
              

                return true;
            }else {
                return false;
            }
        } 
    };
   //  leafletImage(map, function(err, canvas) {
    html2canvas(snapshotelement,config).then(function(canvas) {
      var imgData = canvas.toDataURL("image/png");
      me._dataService.getMapArea(me.obj.moduleCode, me.obj.id, me.obj.resolvedProperties["id_inventor"], imgData);
    });
    
  }catch{console.log('Element could not be drawn on canvas'); }
 
}



}
