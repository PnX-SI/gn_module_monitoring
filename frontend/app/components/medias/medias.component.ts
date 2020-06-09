import { media } from './../upload-media/media';
import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';

import { DataUtilsService } from '../../services/data-utils.service';


@Component({
  selector: 'pnx-medias',
  templateUrl: './medias.component.html',
  styleUrls: ['./medias.component.css']
})
export class MediasComponent implements OnInit {

  bEditMedia = false;
  media;

  @Input() uuid_attached_row;
  @Input() idTableLocation;
  @Input() staticDirUrl;

  @Input() medias = [];
  @Output() mediasChange = new EventEmitter<any>();

  @Input() currentUser;

  constructor(private _dataUtil: DataUtilsService) {}

  ngOnInit() {
  }

  editMedia(media) {
    this.media = media;
    this.bEditMedia = true;
  }

  setMediasType() {
    console.log(this.medias)
    for (const m of this.medias) {
      console.log(m)
      this.setMediaType(m);
    }
  }

  setMediaType(media) {
    media.mediaType = '';
    this._dataUtil.getUtil('nomenclature', media.id_nomenclature_media_type, 'label_fr').subscribe((nomenclature_label) => {
      media.mediaType = nomenclature_label;
    });
  }

  onDeleteMedia(idMedia) {
    console.log('delete Media', idMedia);
    const index = this.medias.findIndex(media => media.id_media === idMedia);
    this.medias.splice(index, 1)
    this.bEditMedia = false;
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
    this.setMediasType()
    this.mediasChange.emit(this.medias);
    this.bEditMedia = false;
  }

  ngOnChanges(changes: SimpleChanges) {
    for (let propName in changes) {
      if(propName === 'medias' && changes[propName].currentValue) {
        this.setMediasType()
      }
      /*let chng = changes[propName];
      let cur  = JSON.stringify(chng.currentValue);
      let prev = JSON.stringify(chng.previousValue);
      this.changeLog.push(`propName: currentValue = cur, previousValue = prev`);*/
    }
  }

}

