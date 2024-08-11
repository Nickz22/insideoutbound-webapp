import { SObject } from "./SObject";
import { ProspectingEffort } from "./ProspectingEffort";
import { ProspectingMetadata } from "./ProspectingMetadata";

export interface Activation {
  id: string;
  account: SObject;
  activated_by_id: string;
  active_contact_ids: Set<string>;
  task_ids: Set<string>;
  activated_date?: Date;
  first_prospecting_activity?: Date;
  last_prospecting_activity?: Date;
  event_ids?: Set<string>;
  prospecting_metadata?: ProspectingMetadata[];
  prospecting_effort?: ProspectingEffort[];
  days_activated?: number;
  days_engaged?: number;
  engaged_date?: Date;
  last_outbound_engagement?: Date;
  opportunity?: SObject;
  status: StatusEnum;
}
