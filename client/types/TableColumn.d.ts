export interface TableColumn {
  id: string;
  dataType: "string" | "number" | "date" | "datetime" | "select" | "image";
  label: string;
  selectedIds?: Set<string>; // only used for `select` column action
}
