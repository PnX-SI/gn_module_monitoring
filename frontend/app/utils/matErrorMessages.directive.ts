import { Component, AfterViewInit, Injector } from '@angular/core';
import { MatInput } from '@angular/material/input';
import { MatFormFieldControl, MatFormField } from '@angular/material/form-field';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: '[matErrorMessages]',
  template: '{{ error }}',
})
export class MatErrorMessagesDirective implements AfterViewInit {
  error = '';
  inputRef: MatFormFieldControl<MatInput>;

  constructor(
    private _inj: Injector,
    private translate: TranslateService
  ) {}

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
      if (firstError === 'required') this.error = this.translate.instant('required');

      if (firstError === 'minlength') this.error = this.translate.instant('MinLength');
    }
  };
}
