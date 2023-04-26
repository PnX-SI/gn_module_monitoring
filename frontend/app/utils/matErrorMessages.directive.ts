import { Component, AfterViewInit, Injector } from '@angular/core';
import {MatInput } from '@angular/material/input';
import { MatFormFieldControl,MatFormField } from '@angular/material/form-field';

@Component({
  selector: '[matErrorMessages]',
  template: '{{ error }}'
})
export class MatErrorMessagesDirective implements AfterViewInit {
  error = '';
  inputRef: MatFormFieldControl<MatInput>;

  constructor(private _inj: Injector) { }

  // Setup all initial tooling
  ngAfterViewInit() {
    // grab reference to MatFormField directive, where form control is accessible.
    let container = this._inj.get(MatFormField);
    this.inputRef = container._control;
    
    // sub to the control's status stream
    this.inputRef.ngControl.statusChanges.subscribe(this.updateErrors);
  }

  // This grabs a single active error instead of multiple.
  private updateErrors = (state: 'VALID' | 'INVALID') => {
    if (state === 'INVALID') {
      let controlErrors = this.inputRef.ngControl.errors;
      const firstError = Object.keys(controlErrors)[0];
      if(firstError === 'required')
        this.error = 'Ce champs est requis.';

      if(firstError === 'minlength')
        this.error = 'Vous devez choisir au moins une valeur.';
    }
  }
}