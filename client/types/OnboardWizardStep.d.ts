import { OnboardWizardStepInput } from "./OnboardWizardStepInput";
import { ApiResponse } from "./ApiResponse";
import { TableColumn } from "./TableColumn";

/**
 * OnboardWizardStep is an interface that defines the structure of the steps in the onboarding wizard.
 * @prop title - The title of the step, shown atop the modal
 * @prop description - The description of the step which is rendered as parsed html in the modal
 * @prop type - The type of the step, "input" for a text/picklist/number input, "table" for a `CustomTable` instance
 * @prop inputs - An array of OnboardWizardStepInput objects that define the input fields for the step
 * @prop renderEval - Function which evaluates to `true` will render this step, used to eval the preceding step based on its label and value
 * @prop dataFetcher - Function that fetches data from the server to populate the table with
 */
export interface OnboardWizardStep {
  title: string;
  description: string;
  type: "input" | "table";
  inputs?: OnboardWizardStepInput[];
  renderEval?: RenderEvaluatorFunction;
  dataFetcher?: DataFetcherFunction;
  columns?: TableColumn[];
}

type RenderEvaluatorFunction = (inputLabel: string, inputValue: string) => void;
type DataFetcherFunction = () => Promise<ApiResponse>;
