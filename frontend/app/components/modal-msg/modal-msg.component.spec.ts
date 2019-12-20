import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ModalMsgComponent } from './modal-msg.component';

describe('ModalMsgComponent', () => {
  let component: ModalMsgComponent;
  let fixture: ComponentFixture<ModalMsgComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ModalMsgComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ModalMsgComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
