import { ApiResponse } from "./ApiResponse";
import { TableColumn } from "./TableColumn";

/**
 * Interface for the input fields in the OnboardWizardStep component, comprised of a simple input field or a selectable table
 * @prop setting - The setting parameter within which the input value will be stored
 * @prop inputType - the type of input
 * @prop inputLabel - The label of the input field
 * @prop options - An array of options for a picklist input
 * @prop renderEval - Function which evaluates to `true` will render this step, used to eval the preceding step based on its label and value
 * @prop dataFetcher - Function that fetches data from the server to populate the table
 * @prop columns - An array of TableColumn objects that define the columns of the table
 */
export interface OnboardWizardStepInput {
  setting: string;
  inputType: "text" | "number" | "picklist" | "table" | "criteria";
  inputLabel?: string;
  options?: string[];
  renderEval?: RenderEvaluatorFunction;
  dataFetcher?: DataFetcherFunction;
  columns?: TableColumn[];
  availableColumns?: TableColumn[];
}

type RenderEvaluatorFunction = (Object) => boolean;
type DataFetcherFunction = (any) => Promise<ApiResponse>;
