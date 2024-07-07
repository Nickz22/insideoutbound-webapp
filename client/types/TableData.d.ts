import { TableColumn } from "./TableColumn";

export interface TableData {
  availableColumns: TableColumn[];
  columns: TableColumn[];
  data: Record<string, any>[];
  selectedIds: Set<string>;
}
