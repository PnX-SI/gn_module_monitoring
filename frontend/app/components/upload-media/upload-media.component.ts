import { FormGroup } from '@angular/forms';
import { HttpResponse, HttpEventType } from '@angular/common/http';
import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormBuilder } from '@angular/forms';

import { UploadService } from './upload.service';
import { DataUtilsService } from '../../services/data-utils.service';

import { mediaFormDefinitionDict } from './media-form-definition';

import { Utils } from '../../utils/utils';

@Component({
  selector: 'pnx-upload-media',
  templateUrl: './upload-media.component.html',
  styleUrls: ['./upload-media.component.css']
})
export class UploadMediaComponent implements OnInit {
  @Input() uuid_attached_row;
  @Input() idTableLocation;

  @Input() media;
  @Output() mediaChange = new EventEmitter<any>();

  @Input() bEditMedia;
  @Output() bEditMediaChange = new EventEmitter<any>();

  @Output() deleteMedia = new EventEmitter<any>();

  @Input() currentUser;

  @Input() staticDirUrl;
  public file: File;
  public description = '';
  public nomenclatureIds = {};
  public mediaForm: FormGroup;
  public mediaFormDefinition = [];

  public bUploadSpinner = false;

  /** Observable pour retourner media au composant */

  constructor(
    private _dataUtilsService: DataUtilsService,
    private _uploadService: UploadService,
    private _formBuilder: FormBuilder
  ) {}

  ngOnInit() {
    for (const cd_nomenclature of ['4', '2']) {
      this._dataUtilsService
        .getNomenclature('TYPE_MEDIA', cd_nomenclature)
        .subscribe(nomenclature => {
          this.nomenclatureIds[cd_nomenclature] = nomenclature['id_nomenclature'];
        });
    }

    // contruit par dynamic form
    this.mediaFormDefinition = Object.keys(mediaFormDefinitionDict).map(key => {
      return { ...{ attribut_name: key }, ...mediaFormDefinitionDict[key] };
    });

    this.mediaForm = this._formBuilder.group({});

    if (this.media) {
      this.setMedia(this.media);
    }
  }

  selectFile(event) {
    const files: FileList = event.target.files;
    if (files && files.length === 0) {
      return;
    }
    const file: File = files[0];
    this.file = file;
  }

  setMedia(media) {
    this.media = media;
    this.media['uuid_attached_row'] = this.media['uuid_attached_row'] || this.uuid_attached_row;
    this.media['id_table_location'] = this.media['id_table_location'] || this.idTableLocation;

    setTimeout(() => {
      const mediaFormValue = {};
      Object.keys(this.mediaForm.controls)
        .forEach((key) => {
          mediaFormValue[key] = media[key] || null;
        }
      );

      this.mediaForm.setValue(mediaFormValue);
    }, 200);
  }

  isMediaFormValid() {
    const condForm = this.mediaForm.valid;
    const condFile = (!!this.file) || (!!this.mediaForm.value['id_media']);
    const condUrl = !!this.mediaForm.value['media_url'];
    return condForm && (condFile || condUrl);
  }

  uploadFile() {
    this.bUploadSpinner = true;
    const postData = this.mediaForm.value;

    this._uploadService.uploadFile(this.file, postData).subscribe(
      event => {
        // media uploadé
        if (event['body']) {
          let media_content = event['body'];

          // Test si c'est un string alors transformation en objet
          // TODO A voir si nécessaire
          if (typeof event['body'] === 'string') {
            media_content = JSON.stringify(event['body']);
          }

          this.media = media_content;
          this.mediaChange.emit(media_content);
          this.bUploadSpinner = false;
        }
        // upload en cours
        if (event.type === HttpEventType.UploadProgress) {
          const percentDone = Math.round((100 * event.loaded) / event.total);
          console.log(`File is ${percentDone}% loaded.`);
        } else if (event instanceof HttpResponse) {
          console.log('File is completely loaded!');
        }
      },
      err => {
        console.log('Upload Error:', err);
      },
      () => {
        console.log('Upload done');
      }
    );
  }

  onDeleteMedia() {
    this._uploadService.deleteMedia(this.media.id_media).subscribe(() => {
      this.deleteMedia.emit(this.media.id_media);
    });
  }

  ngOnChanges(changes) {
    for (const propName of Object.keys(changes)) {
      const chng = changes[propName];
      const cur = chng.currentValue;
      const prev = chng.previousValue;
      if (propName === 'media' && this.mediaForm) {
        this.setMedia(cur);
      }
    }
  }
}
