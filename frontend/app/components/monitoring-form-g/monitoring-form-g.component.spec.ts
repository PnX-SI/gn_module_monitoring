import { MonitoringFormGComponent } from './monitoring-form-g.component';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

describe('MonitoringFormComponent', () => {
  let component: MonitoringFormGComponent;
  let fixture: ComponentFixture<MonitoringFormGComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MonitoringFormGComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MonitoringFormGComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
