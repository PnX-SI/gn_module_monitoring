import { FormGroup } from "@angular/forms";
import { HttpResponse, HttpEventType } from "@angular/common/http";
import { Component, OnInit, Input, Output, EventEmitter } from "@angular/core";
import { FormBuilder } from "@angular/forms";

import { UploadService } from "./upload.service";
import { DataUtilsService } from "../../services/data-utils.service";

import { mediaFormDefinitionDict } from "./media-form-definition";

import { Utils } from "../../utils/utils";

@Component({
  selector: "pnx-upload-media",
  templateUrl: "./upload-media.component.html",
  styleUrls: ["./upload-media.component.css"]
})
export class UploadMediaComponent implements OnInit {
  @Input() uuid_attached_row;
  @Input() id_table_location;

  @Input() media;
  @Output() mediaChange = new EventEmitter<any>();

  @Input() bEditMedia;
  @Output() bEditMediaChange = new EventEmitter<any>();


  @Input() staticDirUrl;
  public file: File;
  public description = "";
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
    for (let cd_nomenclature of ["4", "2"]) {
      this._dataUtilsService
        .getNomenclature("TYPE_MEDIA", cd_nomenclature, "id_nomenclature")
        .subscribe(idNomenclature => {
          this.nomenclatureIds[cd_nomenclature] = idNomenclature;
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
    let files: FileList = event.target.files;
    if (files && files.length == 0) {
      return;
    }
    let file: File = files[0];
    this.file = file;
  }

  setMedia(media) {
    this.media = media;
    this.media["uuid_attached_row"] = this.media["uuid_attached_row"] || this.uuid_attached_row;
    this.media["id_table_location"] = this.media["id_table_location"] || this.id_table_location;
    
    setTimeout(() => {
      let mediaFormValue = {};
      Object.keys(this.mediaForm.controls)
        .forEach((key) => {
          mediaFormValue[key] = media[key] || null;
        }
      );

      this.mediaForm.setValue(mediaFormValue);
    }, 200);
  }

  isMediaFormValid() {
    let condForm = this.mediaForm.valid;
    let condFile = (!!this.file) || (!!this.mediaForm.value["id_media"]);
    let condUrl = !!this.mediaForm.value["media_url"];
    return condForm && (condFile || condUrl);
  }

  uploadFile() {
    this.bUploadSpinner = true;
    let postData = this.mediaForm.value;

    this._uploadService.uploadFile(this.file, postData).subscribe(
      event => {
        // media uploadé
        if (event["body"]) {
          this.media = JSON.parse(event["body"]);
          this.mediaChange.emit(JSON.parse(event["body"]));
          this.bUploadSpinner = false;
        }
        // upload en cours
        if (event.type == HttpEventType.UploadProgress) {
          const percentDone = Math.round((100 * event.loaded) / event.total);
          console.log(`File is ${percentDone}% loaded.`);
        } else if (event instanceof HttpResponse) {
          console.log("File is completely loaded!");
        }
      },
      err => {
        console.log("Upload Error:", err);
      },
      () => {
        console.log("Upload done");
      }
    );
  }

  ngOnChanges(changes) {
    for (let propName in changes) {
      let chng = changes[propName];
      let cur = chng.currentValue;
      let prev = chng.previousValue;
      if (propName == "media" && this.mediaForm) {
        this.setMedia(cur);
      }
    }
  }
}
