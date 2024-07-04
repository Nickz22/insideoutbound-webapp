import { OnboardWizardStepInput } from "./OnboardWizardStepInput";

/**
 * OnboardWizardStep is an interface that defines the structure of the steps in the onboarding wizard.
 * @prop title - The title of the step, shown atop the modal
 * @prop description - The description of the step which is rendered as parsed html in the modal
 * @prop type - The type of the step, "input" for a text/picklist/number input, "table" for a `CustomTable` instance
 * @prop inputs - An array of OnboardWizardStepInput objects that define the input fields for the step
 */
export interface OnboardWizardStep {
  title: string;
  description: string;
  inputs: OnboardWizardStepInput[];
}
