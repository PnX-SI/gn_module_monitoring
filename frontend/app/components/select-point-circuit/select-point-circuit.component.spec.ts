import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SelectPointCircuitComponent } from './select-point-circuit.component';

describe('SelectPointCircuitComponent', () => {
  let component: SelectPointCircuitComponent;
  let fixture: ComponentFixture<SelectPointCircuitComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SelectPointCircuitComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SelectPointCircuitComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
