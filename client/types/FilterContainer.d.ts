import { Filter } from "./Filter";

export interface FilterContainer {
  name: string;
  filters: Filter[];
  filterLogic: string;
}
