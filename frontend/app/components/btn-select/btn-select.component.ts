import { COMMA, ENTER } from '@angular/cdk/keycodes';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { Observable, iif, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, map, startWith, switchMap } from 'rxjs/operators';

import { JsonData } from '../../types/jsondata';

export interface EmptyObject {
  name: string;
}

@Component({
  selector: 'btn-select',
  templateUrl: './btn-select.component.html',
  styleUrls: ['./btn-select.component.css'],
})
export class BtnSelectComponent implements OnInit {
  selectable = true;
  removable = true;
  separatorKeysCodes: number[] = [ENTER, COMMA];
  myControl = new FormControl();
  @Input() placeholderText: string = 'Selectionnez vos options dans la liste';
  @Input() titleBtn: string = 'Choix des options';

  filteredOptions: Observable<any>;
  listOptionChosen: string[] = [];
  configObjAdded: JsonData = {};
  genericResponse: JsonData = {};

  @Input() paramToFilt: string;
  @Input() callBackFunction: (
    pageNumber: number,
    limit: number,
    valueToFilter: string
  ) => Observable<any>;
  @ViewChild('optionInput') optionInput: ElementRef<HTMLInputElement>;

  @Output() public sendobject = new EventEmitter<JsonData>();

  constructor() {}

  ngOnInit() {
    this.filteredOptions = this.myControl.valueChanges.pipe(
      startWith(''),
      debounceTime(400),
      distinctUntilChanged(),
      switchMap((val: string) => {
        return iif(
          () => val == '',
          of([{ name: val }]),
          this.filterOnRequest(val, this.paramToFilt)
        );
      }),
      map((res) => (res.length > 0 ? res : [{ name: 'Pas de résultats' }]))
    );
  }

  remove(option: string): void {
    const index = this.listOptionChosen.indexOf(option);

    if (index >= 0) {
      this.listOptionChosen.splice(index, 1);
    }

    if (this.configObjAdded && this.configObjAdded[option] !== undefined) {
      delete this.configObjAdded[option];
    }
    this.sendobject.emit(this.configObjAdded);
  }

  selected(event: MatAutocompleteSelectedEvent): void {
    const shouldAddValue = this.checkBeforeAdding(event.option.viewValue);
    shouldAddValue
      ? this.listOptionChosen.push(event.option.viewValue) && this.addObject(event.option.value)
      : null;
    this.optionInput.nativeElement.value = '';
    this.myControl.setValue(null);
  }

  filterOnRequest(val: string, keyToFilt: string): Observable<any> {
    return this.callBackFunction(1, 100, val).pipe(
      // Ici on map pour créer une liste d'objet contenant la valeur entré
      map((response) =>
        response.items.filter((option) => {
          return option[keyToFilt].toLowerCase().includes(val.toLowerCase());
        })
      ),
      // Ici on map pour uniformiser la "key" utilisé pour afficher les options (default Key : 'name')
      map((response) =>
        response.filter((obj) => {
          Object.assign(obj, { name: obj[keyToFilt] })[keyToFilt];
          delete obj[keyToFilt];
          return obj;
        })
      )
    );
  }

  checkBeforeAdding(valToAdd: string) {
    const noValidInput = [null, '', 'Pas de résultats'];
    if (noValidInput.includes(valToAdd) || this.listOptionChosen.includes(valToAdd)) {
      return false;
    } else {
      return true;
    }
  }

  addObject(obj: JsonData) {
    const { name, ...configAndId } = obj;
    this.configObjAdded[name] = configAndId;
    this.sendobject.emit(this.configObjAdded);
  }
}
