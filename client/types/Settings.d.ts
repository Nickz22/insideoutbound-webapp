import { FilterContainer } from "./FilterContainer";

export interface Settings {
  inactivityThreshold: number;
  criteria: FilterContainer[];
  meetingObject: string;
  meetingsCriteria: FilterContainer;
  skipAccountCriteria?: FilterContainer;
  skipOpportunityCriteria?: FilterContainer;
  activitiesPerContact: number;
  latestDateQueried: Date;
  contactsPerAccount: number;
  trackingPeriod: number;
  activateByMeeting: boolean;
  activateByOpportunity: boolean;
  teamMemberIds: string[];
  salesforceUserId: string;
}
