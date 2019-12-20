import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MonitoringMapComponent } from './monitoring-map.component';

describe('MonitoringMapComponent', () => {
  let component: MonitoringMapComponent;
  let fixture: ComponentFixture<MonitoringMapComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MonitoringMapComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MonitoringMapComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
