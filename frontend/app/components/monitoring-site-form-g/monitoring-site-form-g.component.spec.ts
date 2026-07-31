import { MonitoringSiteFormGComponent } from './monitoring-site-form-g.component';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

describe('MonitoringSiteFormComponent', () => {
  let component: MonitoringSiteFormGComponent;
  let fixture: ComponentFixture<MonitoringSiteFormGComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MonitoringSiteFormGComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MonitoringSiteFormGComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
