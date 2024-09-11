import {
  fetchEventFilterFields,
  fetchTaskFilterFields,
  fetchSalesforceUsers,
  fetchSalesforceTasksByUserIds,
  fetchSalesforceEventsByUserIds,
} from "./../components/Api/Api";
/**
 * @typedef {import('types').TableData} TableData
 * @typedef {import('types').FilterContainer} FilterContainer
 * @typedef {import('types').CriteriaField} CriteriaField
 * @typedef {import('types').SObject} SObject
 * @typedef {import('types').SObjectField} SObjectField
 * @typedef {import('types').Task} Task
 * @typedef {import('types').OnboardWizardStep} OnboardWizardStep
 * @typedef {import('types').TableColumn} TableColumn
 * @typedef {import('types').Settings} Settings
 * @typedef {import('types').ApiResponse} ApiResponse
 **/

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
/** @type {OnboardWizardStep[]} */
export const ONBOARD_WIZARD_STEPS = [
  {
    description: "",
    title: "Your Role",
    inputs: [
      {
        setting: "userRole",
        inputType: "picklist",
        inputLabel: "User Role",
        options: ["I manage a team", "I am an individual contributor"],
      },
      {
        setting: "teamMemberIds",
        inputType: "table",
        renderEval: (priorInputValues) => {
          return priorInputValues["userRole"] === "I manage a team";
        },
        dataFetcher: async () => {
          return await fetchSalesforceUsers();
        },
        columns: [
          {
            id: "select",
            label: "Select",
            dataType: "select",
          },
          {
            id: "photoUrl",
            label: "",
            dataType: "image",
          },
          {
            id: "firstName",
            label: "First Name",
            dataType: "string",
          },
          {
            id: "lastName",
            label: "Last Name",
            dataType: "string",
          },
          {
            id: "email",
            label: "Email",
            dataType: "string",
          },
          {
            id: "role",
            label: "Role",
            dataType: "string",
          },
          {
            id: "username",
            label: "Username",
            dataType: "string",
          },
        ],
      },
    ],
  },
  {
    description: `
      <h3>Our Goal</h3>
      <p>Our goal is to help you better measure and manage your account-based prospecting efforts. This will allow you to effectively track and optimize your outreach activities to ensure the best results.</p>
      <br>
      <h3>Define Prospecting</h3>
      <p>To do that, <b>we need to define prospecting</b>. The term we use is an \"approach\".</br>Clearly defining an approach helps us differentiate prospecting efforts from all other stuff sales reps do, like working deals or sending one-off emails.</p>
      <br>
      <h3>Please start by filling out the blank below:</h3>
      <p>An "approach" is defined as when a rep attempts to engage with _ people at a target/prospect company within a _ day period.</p>
      <br>
      `,
    title: "Welcome to InsideOutbound",
    inputs: [
      {
        setting: "contactsPerAccount",
        inputType: "number",
        inputLabel: "Number of Engaged People",
      },
      {
        setting: "trackingPeriod",
        inputType: "number",
        inputLabel: "Tracking Period",
      },
    ],
    descriptionRenderer: (description, inputValues) => {
      const values = [
        inputValues?.contactsPerAccount,
        inputValues?.trackingPeriod,
      ];

      return description.replace(/_/g, (match, offset) => {
        const index = description.slice(0, offset).match(/_/g)?.length || 0;
        return values[index] || "_";
      });
    },
  },
  {
    title: "Activities per Contact",
    description: `
      <p>Great — we have a definition for prospecting at the company level! Next, we need to do the same thing for the people who work at target companies.</p>
      <p>Help us fill in the blank below:<br />Once a rep logs _ attempts to contact an individual (emails, calls, InMails, etc.), we consider that "prospecting".</p>
      `,
    inputs: [
      {
        setting: "activitiesPerContact",
        inputType: "text",
        inputLabel: "# activities per contact",
      },
    ],
    descriptionRenderer: (description, inputValues) => {
      if (!inputValues.activitiesPerContact) {
        return description;
      }
      return description.replace(/_/g, inputValues.activitiesPerContact);
    },
  },
  {
    title: "Account Inactivity Threshold",
    description: `
      <p>You're on a roll — we've got a measurable definition for what counts as account-based prospecting!<br />Next up, we\'re going to decide when a prospecting "approach" has ended due to inactivity.</p>
      <p>Help us fill in the blank below:<br />An account should be removed from my prospecting funnel after _ days without a new Task, Event or Opportunity.</p>
      `,
    inputs: [
      {
        setting: "inactivityThreshold",
        inputType: "number",
        inputLabel: "inactivity threshold",
      },
    ],
    descriptionRenderer: (description, inputValues) => {
      if (!inputValues.inactivityThreshold) {
        return description;
      }
      return description.replace(/_/g, inputValues.inactivityThreshold);
    },
  },
  {
    title: "Define an Approach",
    description: `<p>The next few questions will help us understand when to consider an Account 'approached'.</p>`,
    inputs: [
      {
        setting: "activateByOpportunity",
        inputType: "picklist",
        inputLabel: "Activate an Account when an Opportunity is created",
        tooltip:
          "Should the creation of an Opportunity following the creation of a prospecting activity be considered an approach?",
        options: ["Yes", "No"],
      },
      {
        setting: "activateByMeeting",
        inputLabel: "Activate an Account when a Meeting is booked",
        tooltip:
          "Should the creation of a Meeting following the creation of a prospecting activity be considered an approach?",
        inputType: "picklist",
        options: ["Yes", "No"],
      },
      {
        setting: "meetingObject",
        inputType: "picklist",
        inputLabel: "How are meetings recorded?",
        options: [
          "We use the task object for that",
          "We use the event object for that",
        ],
        renderEval: (priorInputValues) => {
          return priorInputValues["activateByMeeting"];
        },
      },
      {
        setting: "meetingsCriteria",
        inputType: "prospectingCriteria",
        inputLabel:
          "Define criteria for Tasks/Events that should set an Account as 'approached'.",
        renderEval: (priorInputValues) => {
          return priorInputValues["meetingObject"] !== undefined;
        },
        dataFetcher: async (settings) => {
          if (!settings.meetingObject) {
            return {
              success: false,
              data: [],
              message: "Meeting object not provided",
            };
          }

          const salesforceUserIds = [
            ...(settings.teamMemberIds || []),
            settings.salesforceUserId,
          ];

          /** @type {TableData} */
          const tableData = {
            columns: [
              {
                id: "select",
                label: "Select",
                dataType: "select",
              },
              {
                id: "Subject",
                label: "Subject",
                dataType: "string",
              },
              {
                id: "Status",
                label: "Status",
                dataType: "string",
              },
            ],
            availableColumns: [],
            data: [],
            selectedIds: new Set(),
          };
          const isEvent = settings.meetingObject.toLowerCase().includes("task")
            ? false
            : true;
          const tableDataResponse = !isEvent
            ? await fetchSalesforceTasksByUserIds(salesforceUserIds)
            : await fetchSalesforceEventsByUserIds(salesforceUserIds);
          tableData.data = tableDataResponse.data.map(
            /** @param {SObject} item */(item) => ({
              ...item,
              id: item.Id,
            })
          );

          const fieldsResponse = !isEvent
            ? await fetchTaskFilterFields()
            : await fetchEventFilterFields();
          tableData.availableColumns = fieldsResponse.data.map(
            /**@param {SObjectField} field*/(field) => ({
              id: field.name,
              label: field.label,
              dataType: field.type,
            })
          );
          return { success: true, data: tableData, message: "" };
        },
        fetchFilterFields: async (settings) => {
          const response =
            settings.meetingObject === "We use the task object for that"
              ? await fetchTaskFilterFields()
              : await fetchEventFilterFields();
          return response.data;
        },
      },
    ],
    descriptionRenderer: (description) => {
      return description;
    },
  },
];
