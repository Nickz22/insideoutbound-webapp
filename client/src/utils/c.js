import {
  generateCriteria,
  fetchEventFilterFields,
  fetchTaskFilterFields,
  fetchSalesforceUsers,
  fetchTaskFields,
  fetchSalesforceTasksByUserIds,
  fetchSalesforceEventsByUserIds,
  fetchEventFields,
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
    title: "Tell us about yourself",
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
      Our goal is to help you better measure and manage your account-based prospecting efforts. 
      <br><br> 
      To do that, <b>we need to define prospecting</b>. The term we use is an \"approach\". 
      Clearly defining an approach helps us differentiate prospecting efforts from all other stuff sales reps do, like working deals or sending one-off emails.
      <br><br>
      Please start by filling out the blanks below: 
      <br><br>
      An "approach" is defined as when a rep attempts to engage with _ people at a target/prospect company within a _ day period.
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
        inputValues.contactsPerAccount,
        inputValues.trackingPeriod,
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
      Great — we have a definition for prospecting at the company level! Next, we need to do the same thing for the people who work at target companies. 
      Help us fill in the blank below: 
      <br><br>
      Once a rep logs _ attempts to contact an individual (emails, calls, InMails, etc.), we consider that "prospecting".
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
      You're on a roll — we've got a measurable definition for what counts as account-based prospecting!
      <br><br>
      Next up, we\'re going to decide when a prospecting "approach" has ended due to inactivity.
      Help us fill in the blank below:
      <br><br>
      An account should be removed from my prospecting funnel after _ days of inactivity.
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
    description: `
    The next few questions will help us understand when to consider an Account "approached".
    <br><br>
    First, are meetings a strong indication of an Account being 'approached'?
    `,
    inputs: [
      {
        setting: "activateByMeeting",
        inputType: "picklist",
        options: ["Yes", "No"],
      },
      {
        setting: "meetingObject",
        inputType: "picklist",
        inputLabel: "How are meetings recorded?",
        options: [
          "We have an opportunity stage for that",
          "We use the task object for that",
          "We use the event object for that",
        ],
        renderEval: (priorInputValues) => {
          return priorInputValues["activateByMeeting"] === "Yes";
        },
      },
      {
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
          {
            id: "TaskSubtype",
            label: "TaskSubtype",
            dataType: "string",
          },
        ],
        availableColumns: (await fetchTaskFields()).data.map(
          /** @param {SObjectField} field */
          (field) => ({
            id: field.name,
            label: field.label,
            dataType: field.type,
          })
        ),
        setting: "",
        inputLabel:
          "Select Tasks that should set an Account as 'approached'. We'll create filters from your selections - don't worry, you'll have a chance to confirm them later.",
        inputType: "table",
        renderEval: (priorInputValues) => {
          return (
            priorInputValues["meetingObject"] ===
            "We use the task object for that"
          );
        },
        dataFetcher:
          /** @param {Settings} settings */
          async (settings) => {
            if (!settings.meetingObject) {
              return {
                success: false,
                data: [],
                message: "Meeting object not provided",
              };
            }

            /** @type {string[]} */
            const salesforceUserIds = [
              ...(settings.teamMemberIds || []),
              settings.salesforceUserId,
            ];
            const response = await fetchSalesforceTasksByUserIds(
              salesforceUserIds
            );
            response.data = response.data.map(
              /** @param {SObject} task */
              (task) => ({ ...task, id: task.Id })
            );
            return response;
          },
      },
      {
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
            id: "EventSubtype",
            label: "Event Subtype",
            dataType: "string",
          },
          {
            id: "Type",
            label: "Type",
            dataType: "string",
          },
        ],
        availableColumns: (await fetchEventFields()).data.map(
          /** @param {SObjectField} field */
          (field) => ({
            id: field.name,
            label: field.label,
            dataType: field.type,
          })
        ),
        setting: "",
        inputType: "table",
        inputLabel:
          "Select Events that should set an Account as 'approached'. We'll create filters from your selections - don't worry, you'll have a chance to confirm them later.",
        renderEval: (priorInputValues) => {
          return (
            priorInputValues["meetingObject"] ===
            "We use the event object for that"
          );
        },
        dataFetcher:
          /** @param {Settings} settings */
          async (settings) => {
            if (!settings.meetingObject) {
              return {
                success: false,
                data: [],
                message: "Meeting object not provided",
              };
            }

            /** @type {string[]} */
            const salesforceUserIds = [
              ...(settings.teamMemberIds || []),
              settings.salesforceUserId,
            ];

            const response = await fetchSalesforceEventsByUserIds(
              salesforceUserIds
            );
            response.data = response.data.map(
              /** @param {SObject} event */
              (event) => ({ ...event, id: event.Id })
            );
            return response;
          },
      },
      {
        setting: "meetingsCriteria",
        inputType: "criteria",
        renderEval: (tableData) => {
          return tableData && tableData["selectedIds"]
            ? Array.from(tableData["selectedIds"]).length > 0
            : false;
        },
        dataFetcher:
          /**
           * @param {TableData} tableData
           * @return {Promise<ApiResponse>}
           **/
          async (tableData) => {
            const criteriaResponse = await generateCriteria(
              tableData.data.filter((record) =>
                tableData.selectedIds.has(record.Id)
              ),
              tableData.columns
            );
            const filterFieldsResponse = Array.from(
              tableData.selectedIds
            )[0].startsWith("00T")
              ? await fetchTaskFilterFields()
              : await fetchEventFilterFields();

            return {
              success: criteriaResponse.success && filterFieldsResponse.success,
              message: criteriaResponse.message || filterFieldsResponse.message,
              data: [
                {
                  filterContainer: criteriaResponse.data[0],
                  filterFields: filterFieldsResponse.data,
                  filterOperatorMapping: FILTER_OPERATOR_MAPPING,
                  hasNameField: true,
                },
              ],
            };
          },
      },
    ],
    descriptionRenderer: (description) => {
      return description;
    },
  },
];
