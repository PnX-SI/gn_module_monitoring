import { MonitoringFormComponent } from './monitoring-form.component';
import { ComponentFixture, TestBed, async } from '@angular/core/testing';

describe('MonitoringFormComponent', () => {
  let component: MonitoringFormComponent;
  let fixture: ComponentFixture<MonitoringFormComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MonitoringFormComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MonitoringFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
