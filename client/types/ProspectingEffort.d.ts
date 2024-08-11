import { ProspectingMetadata } from "./ProspectingMetadata";

export interface ProspectingEffort {
  activation_id: string;
  prospecting_metadata: ProspectingMetadata[];
  status: string;
  date_entered: Date;
  task_ids: Set<string>;
}
