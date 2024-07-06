import { FilterContainer } from "./FilterContainer";

export interface Settings {
  inactivityThreshold: number;
  cooloffPeriod: number;
  criteria: FilterContainer[];
  meetingObject: string;
  meetingsCriteria: FilterContainer;
  skipAccountCriteria?: FilterContainer;
  skipOpportunityCriteria?: FilterContainer;
  activitiesPerContact: number;
  contactsPerAccount: number;
  trackingPeriod: number;
  activateByMeeting: boolean;
  activateByOpportunity: boolean;
  teamMemberIds: string[];
  salesforceUserId: string;
}
