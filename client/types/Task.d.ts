export interface Task {
  id: string;
  createdDate: Date;
  whoId: string;
  subject: string;
  status: string;
  taskSubtype?: string;
}
