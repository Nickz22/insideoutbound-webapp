/** @type {{ [key: string]: {[key:string]: string} }}} */
export const FILTER_OPERATOR_MAPPING = {
  string: {
    contains: "LIKE",
    equals: "=",
    "not equals": "!=",
  },
  int: {
    equals: "=",
    "not equals": "!=",
    "less than": "<",
    "less than or equal": "<=",
    "greater than": ">",
    "greater than or equal": ">=",
  },
  picklist: {
    contains: "LIKE",
    equals: "=",
    "not equals": "!=",
  },
};

export const PROSPECTING_ACTIVITY_FILTER_TITLE_PLACEHOLDERS = [
  "Outbound Calls",
  "LinkedIn Messages",
  "Inbound Calls",
  "Gifts",
  "Outbound Emails",
  "Inbound Emails",
  "LinkedIn Connections",
  "Meetings",
  "Webinars",
  "Conferences",
];

export const MOCK_TASK_DATA = [
  {
    Id: 1,
    Subject: "Call John Doe",
    Who: "John Doe",
    Priority: "High",
    Status: "Not Started",
    Type: "Call",
    TaskSubtype: "Email",
  },
  {
    Id: 2,
    Subject: "Email Jane Doe",
    Who: "Jane Doe",
    Priority: "High",
    Status: "Not Started",
    Type: "Email",
    TaskSubtype: "Email",
  },
  {
    Id: 3,
    Subject: "Call John Smith",
    Who: "John Smith",
    Priority: "Low",
    Status: "Not Started",
    Type: "Call",
    TaskSubtype: "Call",
  },
  {
    Id: 4,
    Subject: "Email Jane Smith",
    Who: "Jane Smith",
    Priority: "High",
    Status: "Not Started",
    Type: "Email",
    TaskSubtype: "Call",
  },
];

/**
 * @typedef {import('types').OnboardWizardStep} OnboardWizardStep
 */

/** @type {Array<OnboardWizardStep | OnboardWizardStep[]>} */
export const ONBOARD_WIZARD_STEPS = [
  {
    title: "Tracking Period",
    setting: "trackingPeriod",
    description: "How long should an Account be actively pursued?",
    inputType: "number",
    inputLabel: "Number of days",
  },
  {
    title: "Inactivity Threshold",
    setting: "inactivityThreshold",
    description:
      "How many days can an Account have no prospecting activity before it should be considered inactive?",
    inputType: "number",
    inputLabel: "Number of days",
  },
  {
    title: "Cooloff Period",
    setting: "cooloffPeriod",
    description: "How much time should pass before re-engaging?",
    inputType: "number",
    inputLabel: "Number of days",
  },
  {
    title: "Contacts per Account",
    setting: "contactsPerAccount",
    description:
      "How many Contacts under a single Account need to be prospected before the Account is considered to be engaged?",
    inputType: "number",
    inputLabel: "Number of Contacts",
  },
  {
    title: "Acivities per Contact",
    setting: "activitiesPerContact",
    description:
      "How many prospecting activities are needed under a single Contact before it can be considered prospected?",
    inputType: "number",
    inputLabel: "Number of Activities",
  },
  [
    {
      title: "Meetings",
      setting: "meetingObject",
      description: "Are meetings logged as Tasks or Events?",
      inputType: "picklist",
      inputLabel: "Meeting Object",
      options: ["Task", "Event"],
    },
    {
      title: "",
      inputLabel: "",
      inputType: "filterContainer",
      setting: "meetingsCriteria",
      description: "Configure filters for meeting engagement",
      defaultFilterName: "Meeting Criteria",
    },
    {
      title: "",
      description:
        "Should an Account be immediately considered as engaged when a meeting is booked with one of its Contacts?",
      setting: "activateByMeeting",
      inputType: "boolean",
      inputLabel: "Automatically Engage via Meetings",
    },
  ],
  {
    title: "Automatically Engage via Opportunities",
    setting: "activateByOpportunity",
    description:
      "Should an Account be immediately considered as engaged when an Opportunity is created?",
    inputType: "boolean",
    inputLabel: "Automatically Engage via Opportunities",
  },
];
