import { Filter } from "./Filter";
import { Settings } from "./Settings";
import { SObject } from "./SObject";

export type RequiredProspectingCategory =
  | "Inbound Call"
  | "Outbound Call"
  | "Inbound Email"
  | "Outbound Email";

type OnboardFilter = {
  name: RequiredProspectingCategory;
  filters: Filter[];
  filterLogic: string;
  direction: "Inbound" | "Outbound";
};

export type GatheringResponses = Record<string, any>;
export type CategoryFormTableData = {
  availableColumns: any[];
  columns: any[];
  data: any[];
  selectedIds: Set<any>;
};

export interface OnboardContextInit {
  filters: OnboardFilter[];
  step: number;
  gatheringResponses;
  isLargeDialog: boolean;
  isTransitioning: boolean;
  categoryFormTableData: CategoryFormTableData;
  tasks: SObject[];
  inputValues: Partial<Settings>;
}

export interface OnboardContextValue {
  filters: OnboardFilter[];
  step: number;
  gatheringResponses;
  isLargeDialog: boolean;
  isTransitioning: boolean;
  categoryFormTableData: CategoryFormTableData;
  tasks: SObject[];
  inputValues: Partial<Settings>;
  setFilters: React.Dispatch<React.SetStateAction<OnboardFilter[]>>;
  setStep: React.Dispatch<React.SetStateAction<number>>;
  setGatheringResponses: React.Dispatch<
    React.SetStateAction<GatheringResponses>
  >;
  setIsLargeDialog: React.Dispatch<React.SetStateAction<boolean>>;
  setIsTransitioning: React.Dispatch<React.SetStateAction<boolean>>;
  setCategoryFormTableData: React.Dispatch<
    React.SetStateAction<CategoryFormTableData>
  >;
  setTasks: React.Dispatch<React.SetStateAction<SObject[]>>;
  setInputValues: React.Dispatch<React.SetStateAction<Partial<Settings>>>;
  handleStepClick: (clickedStep: number) => void;
}
