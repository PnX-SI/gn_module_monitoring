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

// Interface pour typer la configuration de html2canvas
interface Html2CanvasConfig {
  allowTaint: boolean;
  useCORS: boolean;
  logging: boolean;
  ignoreElements: (element: HTMLElement) => boolean;
}

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
    // Si les permissions n'ont pas été initialisées
    this.userPermission =
      this.currentUser.moduleCruved ||
      this.permissionService.setModulePermissions(this._configServiceG.moduleCode() || 'generic');
  }

  hasEditPermission(): boolean {
    const objectCruved = this.obj?.cruved ?? {};
    const userPermission = this.userPermission?.[this.objectType] ?? {};
    return (objectCruved['U'] ?? 0) > 0 || (userPermission['U'] ?? 0) > 0;
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
    this._dataService.getExportCsv(this.moduleCode, exportDef.method, queryParams);
  }

  /**
   * Exporte un élément DOM en PDF en utilisant html2canvas.
   * Capture l'élément avec l'ID 'geometry', applique des filtres pour exclure certains éléments,
   * puis envoie les données au service d'export PDF.
   *
   * @param exportPdfConfig - Configuration spécifique pour l'export PDF (ex: template).
   * @throws Affiche une erreur via un toaster si une exception est levée.
   */
  processExportPdf(exportPdfConfig: { template: string }): void {
    try {
      // Récupération de l'élément DOM à exporter
      const snapshotElement = document.getElementById('geometry');
      if (!snapshotElement) {
        throw new Error("L'élément 'geometry' est introuvable dans le DOM.");
      }

      //  Configuration de html2canvas pour ignorer certains éléments (contrôles Leaflet, etc.)
      const html2CanvasConfig: Html2CanvasConfig = {
        allowTaint: true, // Autorise les images cross-origin
        useCORS: true, // Active le support CORS pour les images
        logging: false, // Désactive les logs de débogage
        ignoreElements: (element: HTMLElement) => {
          // Liste des éléments à exclure de la capture
          const excludedClasses = [
            'leaflet-control-zoom-in',
            'leaflet-control-zoom-out',
            'leaflet-control-layers-toggle',
          ];
          const excludedAttributes = [
            { attribute: 'title', value: 'A JS library for interactive maps' },
            { attribute: 'placeholder', value: 'Rechercher un lieu' },
          ];

          // Vérifie si l'élément a une classe ou un attribut exclu
          return (
            excludedClasses.includes(element.classList[0]) ||
            excludedAttributes.some(
              ({ attribute, value }) => element.getAttribute(attribute) === value
            )
          );
        },
      };

      // Capture de l'élément en canvas
      html2canvas(snapshotElement, html2CanvasConfig)
        .then((canvas: HTMLCanvasElement) => {
          // Conversion du canvas en image PNG (base64)
          const imgData = canvas.toDataURL('image/png');

          // Préparation des données supplémentaires pour l'export
          const objectId =
            this.obj[this._configServiceG.config()?.[this.objectType]?.id_field_name];
          if (!objectId) {
            throw new Error("L'ID de l'objet est introuvable.");
          }

          const extraData = {
            resolved_properties: this.obj,
          };

          // Appel au service pour générer le PDF
          this._dataService
            .postPdfExport(
              this.moduleCode,
              this.objectType,
              objectId,
              exportPdfConfig.template,
              imgData,
              extraData
            )
            .subscribe({
              next: () => {
                // 7. Notification de succès
                this._commonService.regularToaster(
                  'success',
                  "L'export PDF est prêt à être récupéré dans le dossier de Téléchargement"
                );
              },
              error: (error) => {
                // Gestion des erreurs du service
                console.error("Erreur lors de l'export PDF :", error);
                this._commonService.regularToaster(
                  'error',
                  "Une erreur est survenue lors de l'envoi des données pour l'export PDF."
                );
              },
            });
        })
        .catch((error) => {
          // Gestion des erreurs de html2canvas
          console.error('Erreur lors de la capture du canvas :', error);
          this._commonService.regularToaster(
            'error',
            "Une erreur est survenue lors de la capture de l'élément pour l'export PDF."
          );
        });
    } catch (error) {
      //  Gestion des erreurs générales (ex: élément DOM manquant)
      console.error("Erreur générale lors de l'export PDF :", error);
      this._commonService.regularToaster('error', "Une erreur est survenue durant l'export PDF.");
    }
  }
}
