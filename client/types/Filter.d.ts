import { PicklistOption } from "./PicklistOption";
export interface Filter {
  field: string;
  operator: string;
  value: string;
  dataType: string;
  options?: PicklistOption[];
}
