export interface OnboardWizardStep {
  title: string;
  setting: string;
  description: string;
  inputType: "number" | "picklist" | "filterContainer" | "boolean" | "text";
  inputLabel: string;
  options?: string[];
  defaultFilterName?: string;
}
