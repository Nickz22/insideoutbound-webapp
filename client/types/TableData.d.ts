import { TableColumn } from "./TableColumn";

export interface TableData {
  columns: TableColumn[];
  data: Record<string, any>[];
  selectedIds: Set<string>;
}
