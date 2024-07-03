import { Contact } from './Contact';
export interface Task {
  id: string;
  createdDate: Date;
  who: Contact;
  subject: string;
  status: string;
  priority: string;
  type: string;
  taskSubtype: string;
}
