export interface TemplateData {
    fieldNames:string[];
    fieldLabels:Record<string,string>;
    fieldDefinitions: Record<string,string>;
    childType:string[];
    exportPDF:any;
    exportCSV:any;
}