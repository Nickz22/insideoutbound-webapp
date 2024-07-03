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

/** @type {Array<OnboardWizardStep>} */
export const ONBOARD_WIZARD_STEPS = [
  {
    title: "Welcome to InsideOutbound!",
    description:
      "Our goal is to help you better measure and manage your account-based prospecting efforts.",
    setting: "defineProspecting",
    inputType: "text",
    inputLabel:
      'An "approach" is defined as when a rep attempts to engage with __ people at a target/prospect company within a __ day period.',
  },
  {
    title: "Great — we have a definition for prospecting at the company level!",
    description:
      "Next, we need to do the same thing for the people who work at target companies.",
    setting: "defineProspectingIndividual",
    inputType: "text",
    inputLabel:
      'Once a rep logs __ attempts to contact an individual (emails, calls, InMails, Etc), we consider that "prospecting".',
  },
  {
    title:
      "You're on a roll — we've got a measurable definition for what counts as account-based prospecting!",
    description:
      'Next up, we\'re going to decide when a prospecting "approach" has ended due to inactivity.',
    setting: "inactivityThreshold",
    inputType: "number",
    inputLabel:
      "An account should be removed from my prospecting funnel after __ days of inactivity.",
  },
  {
    title:
      'You\'ve decided what constitutes an "approach" as well as when we should stop tracking an approach due to inactivity.',
    description:
      "Most companies that do account-based prospecting approach companies more than once if they don't buy the first time you prospect them.",
    setting: "cooloffPeriod",
    inputType: "number",
    inputLabel:
      "Once an approach ends, how long should your cooling off period be? When in doubt, we suggest 30 days.",
  },
  {
    title:
      "Now let's talk about the fun stuff — when your approaches are successful!",
    description: "First, how are meetings recorded in your CRM?",
    setting: "meetingObject",
    inputType: "picklist",
    inputLabel: "Meeting recording method",
    options: [
      "We have an opportunity stage for that.",
      "We use the task object for that",
      "We use the event object for that",
      "A custom object record is created",
      "I'm not sure...I need help with this one",
    ],
  },
  {
    title: "Moving on to opportunities...",
    description: "Which of the following is most true for your team?",
    setting: "opportunityCreation",
    inputType: "picklist",
    inputLabel: "Opportunity creation process",
    options: [
      "Opportunities are created by one team, then passed to another.",
      "The rep who creates the opportunity keeps it and works it through close.",
      "It depends on the team.",
    ],
  },
];
