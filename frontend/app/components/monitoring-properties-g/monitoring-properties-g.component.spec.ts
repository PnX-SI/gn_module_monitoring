import { MonitoringPropertiesComponent } from './monitoring-properties-g.component';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

describe('MonitoringPropertiesGComponent', () => {
  let component: MonitoringPropertiesComponent;
  let fixture: ComponentFixture<MonitoringPropertiesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MonitoringPropertiesComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MonitoringPropertiesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
