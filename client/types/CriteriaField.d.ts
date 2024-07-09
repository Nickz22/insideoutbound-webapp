import { PicklistOption } from "./PicklistOption";

export interface CriteriaField {
  name: string;
  type: string;
  options: PicklistOption[];
}
