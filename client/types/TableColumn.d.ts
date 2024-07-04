export interface TableColumn {
  id: string;
  dataType: "string" | "number" | "date" | "datetime" | "select" | "image";
  label: string;
}
