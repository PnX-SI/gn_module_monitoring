import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'pnx-medias',
  templateUrl: './medias.component.html',
  styleUrls: ['./medias.component.css']
})
export class MediasComponent implements OnInit {

  bEditMedia = false;
  media;

  @Input() uuid_attached_row;
  @Input() id_table_location;
  @Input() staticDirUrl;

  @Input() medias = [];
  @Output() mediasChange = new EventEmitter<any>();

  constructor() { }

  ngOnInit() {

  }

  editMedia(media) {
    this.media = media;
    this.bEditMedia = true;
  }

  onMediaChange(mediaChanged) {
    this.media = mediaChanged;
    let isNewMedia = true;
    this.medias.forEach((media, index) => {
      if (media.id_media === this.media.id_media) {
        this.medias[index] = this.media;
        isNewMedia = false;
      }
    });
    if (isNewMedia) {
      this.medias.push(mediaChanged);
    }
    this.mediasChange.emit(this.medias);
    this.bEditMedia = false;
  }

}
