export interface OnboardWizardStepInput {
  setting: string;
  inputType: "text" | "number" | "picklist";
  inputLabel: string;
  options?: string[];
}
