import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DrawFormComponent } from './draw-form.component';

describe('DrawFormComponent', () => {
  let component: DrawFormComponent;
  let fixture: ComponentFixture<DrawFormComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DrawFormComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DrawFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
