import { JsonData } from "../types/jsondata";
export interface ResponseUpdated {
  message: string;
  payload: JsonData;
  status_code: number;
}
