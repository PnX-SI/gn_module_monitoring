import { Component, ViewChild, Input, Output, EventEmitter } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatMenuTrigger } from '@angular/material/menu';
import { SelectObject } from '../../interfaces/object';
import { ObjectService } from '../../services/object.service';

@Component({
  selector: 'option-list-btn',
  templateUrl: './option-list-btn.component.html',
  styleUrls: ['./option-list-btn.component.css'],
})
export class OptionListButtonComponent {
  @ViewChild(MatMenuTrigger) ddTrigger: MatMenuTrigger;

  form = new FormControl();
  private _optionList: SelectObject[];
  @Input() set optionList(value: SelectObject[]) {
    this._optionList = value;
  }

  get optionList(): SelectObject[] {
    // other logic
    return this._optionList;
  }
  @Input() label: string = '';
  @Input() placeholder: string = '';
  @Input() iconOrButton: string = 'button';
  @Output() onSaved = new EventEmitter<SelectObject>();
  @Output() onDeployed = new EventEmitter<any>();

  @Input() item: [];

  constructor(private _objService: ObjectService) {}

  cancelClick(ev: MouseEvent) {
    ev.stopPropagation();
  }

  onCancel() {
    this.ddTrigger.closeMenu();
  }

  onSave() {
    this.ddTrigger.closeMenu();
    this.onSaved.emit(this.form.value);
    //
  }

  onDeploy() {
    if (this.item) {
      this.onDeployed.emit(this.item);
      this._objService.currentListOption.subscribe((optionList) => (this._optionList = optionList));
    }
    this.onDeployed.emit();
  }

  displayFn(value: SelectObject) {
    if (value) {
      return value.label;
    }
  }
}
