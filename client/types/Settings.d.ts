import { TabsOwnProps } from "@mui/material";
import { FilterContainer } from "./FilterContainer";

export interface Settings {
  inactivityThreshold: number;
  criteria: FilterContainer[];
  meetingObject: string;
  meetingsCriteria: FilterContainer;
  activitiesPerContact: number;
  contactsPerAccount: number;
  trackingPeriod: number;
  activateByMeeting: boolean;
  activateByOpportunity: boolean;
  userRole: string;
  teamMemberIds: string[];
  latestDateQueried: datetime;
  skipAccountCriteria?: FilterContainer;
  skipOpportunityCriteria?: FilterContainer;
  salesforceUserId?: string;
}

export interface SettingStatus {
  saving: boolean;
  saveSuccess: boolean;
  isLoading: boolean;
  isTableLoading: boolean;
  setSaving?: Dispatch<SetStateAction<boolean>>;
  setSaveSuccess?: Dispatch<SetStateAction<boolean>>;
  setIsLoading?: Dispatch<SetStateAction<boolean>>;
  setIsTableLoading?: Dispatch<SetStateAction<boolean>>;
}

export interface SettingFilter {
  taskFilterFields: any[];
  eventFilterFields: any[];
  setTaskFilterFields?: Dispatch<SetStateAction<any[]>>;
  setEventFilterFields?: Dispatch<SetStateAction<any[]>>;
}

export interface SettingsContextValue {
  settings: Settings;
  setSettings?: Dispatch<SetStateAction<string | null>>;
  status: SettingStatus;
  currentTab: number;
  setCurrentTab?: Dispatch<SetStateAction<number | null>>;
  handleTabChange?: TabsOwnProps["onChange"];
  filter: SettingFilter;
  criteria: Settings["criteria"];
  setCriteria?: Dispatch<SetStateAction<Settings["criteria"]>>;
  fetchTeamMembersData?: (selectedIds: string[]) => Promise<void>;
  handleChange?: (field: string, value: string | number | boolean) => void;
  formatDateForInput?: (date: Date) => void;
  handleCriteriaChange?: (index: number, value: FilterContainer) => void;
  handleDeleteFilter: (index: number) => void;
  handleAddCriteria: () => void;
}
