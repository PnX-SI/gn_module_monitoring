import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  SimpleChanges,
} from "@angular/core";
import { FormControl } from "@angular/forms";
import { extendedDetailsSiteGroup } from "../../class/monitoring-sites-group";
import { ISitesGroup } from "../../interfaces/geom";
import { EditObjectService } from "../../services/edit-object.service";
import { ObjectService } from "../../services/object.service";

@Component({
  selector: "pnx-monitoring-properties-g",
  templateUrl: "./monitoring-properties-g.component.html",
  styleUrls: ["./monitoring-properties-g.component.css"],
})
export class MonitoringPropertiesGComponent implements OnInit {
  @Input() selectedObj: ISitesGroup;
  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();
  @Input() objectType: string;

  infosColsSiteGroups: typeof extendedDetailsSiteGroup =
    extendedDetailsSiteGroup;
  color: string = "white";
  dataDetails: ISitesGroup;

  datasetForm = new FormControl();

  constructor(
    private _editService: EditObjectService,
    private _objService: ObjectService
  ) {}

  ngOnInit() {
    this._objService.currentObjectTypeParent.subscribe((newObjType) => {
      this.objectType = newObjType;
    });
  }

  onEditClick() {
    this.bEditChange.emit(true);
    this.selectedObj["id"] = this.selectedObj[this.selectedObj.pk];
    this._editService.changeDataSub(this.selectedObj);
  }
}
