import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { ApiService } from '../../services/api-geom.service';
import { MonitoringObjectG } from '../../class/monitoring-object-g';
import {
  FormGroup,
  FormBuilder,
  Validators,
  FormControl,
  FormArray,
} from '@angular/forms';
import { CommonService } from '@geonature_common/service/common.service';

@Component({
  selector: 'pnx-monitoring-form-g',
  templateUrl: './monitoring-form-g.component.html',
  styleUrls: ['./monitoring-form-g.component.css'],
})
export class MonitoringFormGComponent implements OnInit {
    @Input() apiService: ApiService;
    @Input() obj: MonitoringObjectG;
    @Input() form: FormGroup;

    public saveAndAddChildrenSpinner: boolean = false;
    public saveSpinner: boolean = false;
    public chainInput: boolean = false;
    public canUpdate: boolean = false;
    public addChildren: boolean = false;

    constructor(public _commonService: CommonService) {
    }
    
    ngOnInit() {

    }

    initForm() {
        
    }

    notAllowedMessage() {

    }

    onSubmit(isAddChildrend = false) {
        isAddChildrend
            ? (this.saveAndAddChildrenSpinner = true)
            : (this.saveSpinner = true);

        let objFormValueGroup = this.form.value;
    
        let actionLabel = "";
        let action; 
        if (this.obj) {
            action = this.apiService.patch;
            actionLabel = 'Modification'
        } else {
            action = this.apiService.create;
            actionLabel = 'Création'
        }

        action.subscribe((objData) => {
            this._commonService.regularToaster('success', actionLabel);
            this.saveSpinner = this.saveAndAddChildrenSpinner = false;
            /** si c'est un module : reset de la config */
            // if (this.obj.objectType === 'module') {
            //     this._configService.loadConfig(this.obj.moduleCode).subscribe();
            // }
    
            if (this.chainInput) {
                console.log("this.resetObjForm()");
                // this.resetObjForm();
            } else if (isAddChildrend) {
                console.log("this.navigateToAddChildren()");
                // this.navigateToAddChildren();
            } else {
                if (true) {
                // if (this.obj.configParam('redirect_to_parent')) {
                    console.log("this.navigateToParent()");
                    // this.navigateToParent();
                } else {
                    console.log("this.navigateToDetail()");
                    // this.navigateToDetail();
                }
            }
        });
    }

    onCancelEdit() {

    }
}