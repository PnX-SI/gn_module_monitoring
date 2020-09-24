import { Component, OnInit, Input } from '@angular/core';


@Component({
  selector: 'pnx-modal-msg',
  templateUrl: './modal-msg.component.html',
  styleUrls: ['./modal-msg.component.css']
})
export class ModalMsgComponent implements OnInit {

  @Input() bDisplayModal;

  constructor() { }

  ngOnInit() {
  }

}
