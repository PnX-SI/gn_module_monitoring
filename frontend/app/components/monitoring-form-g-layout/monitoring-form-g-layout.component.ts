import { Component, Input, Output, EventEmitter } from '@angular/core';
import { FormGroup } from '@angular/forms';

import { JsonData } from '../../types/jsondata';

/**
 * Cadre commun (modale de suppression, toggle chaînage, formulaire, boutons)
 * partagé par pnx-monitoring-form-g et pnx-monitoring-site-form-g.
 * Les champs du formulaire sont fournis via ng-content par le composant appelant.
 */
@Component({
  selector: 'pnx-monitoring-form-g-layout',
  templateUrl: './monitoring-form-g-layout.component.html',
  styleUrls: ['./monitoring-form-g-layout.component.css'],
})
export class MonitoringFormGLayoutComponent {
  @Input() formsDefinition: JsonData;
  @Input() object: any;
  @Input() config: any;
  @Input() objectType: String;
  @Input() form: FormGroup;
  @Input() chainInput: boolean;
  @Input() saveSpinner: boolean;
  @Input() saveAndAddChildrenSpinner: boolean;
  @Input() canUpdate: boolean;
  @Input() canDelete: boolean;
  @Input() toolTipNotAllowed: string;
  @Input() addChildren: boolean;
  @Input() deleteSpinner: boolean;
  @Input() deleteModal: boolean;

  @Output() chainInputChange = new EventEmitter<boolean>();
  @Output() deleteModalChange = new EventEmitter<boolean>();
  @Output() submitForm = new EventEmitter<boolean>();
  @Output() notAllowed = new EventEmitter<void>();
  @Output() cancelEdit = new EventEmitter<void>();
  @Output() confirmDelete = new EventEmitter<void>();
}
