import { createContext, useCallback, useContext, useState } from "react";
import { useSettingUtil } from "./useSettingUtil";

/** @typedef {import("types/Settings").SettingsContextValue} SettingsContextValue */
/** @typedef {import("types/FilterContainer").FilterContainer} FilterContainer */
/** @typedef {import("types/TableData").TableData} TableData */
/** @typedef {import("types/TableColumn").TableColumn} TableColumn */

/** @type {FilterContainer} */
const initMeetingsCriteria = { filters: [], filterLogic: "", name: "" };

/** @type {FilterContainer[]} */
const initCriteria = [];

/** @type {string[]} */
const initTeamMemberIds = [];

/** @type {any[]} */
const initEventFilterFields = [];

/** @type {any[]} */
const initTaskFilterFields = [];

/** @returns {TableData | null}  */
const initTableData = () => {
  return null;
};

/** @type {import("types/Settings").Settings} */
const initSettings = {
  inactivityThreshold: 0,
  criteria: initCriteria,
  meetingObject: "",
  meetingsCriteria: initMeetingsCriteria,
  activitiesPerContact: 0,
  contactsPerAccount: 0,
  trackingPeriod: 0,
  activateByMeeting: Boolean(false),
  activateByOpportunity: Boolean(false),
  userRole: "",
  teamMemberIds: initTeamMemberIds,
  latestDateQueried: null,
};

/** @type {import("react").Context<SettingsContextValue>} */
const SettingsContext = createContext({
  settings: initSettings,
  criteria: initCriteria,
  status: {
    isLoading: Boolean(false),
    isTableLoading: Boolean(false),
    saveSuccess: Boolean(false),
    saving: Boolean(false),
  },
  currentTab: 0,
  filter: {
    eventFilterFields: initEventFilterFields,
    taskFilterFields: initTaskFilterFields,
  },
  handleChange: (field, value) => {
    field;
    value;
    return;
  },
  formatDateForInput: (date) => {
    date;
    return;
  },
  handleCriteriaChange: (index, value) => {
    index;
    value;
    return;
  },
  fetchTeamMembersData: async (selectedIds) => {
    selectedIds;
    return;
  },
  handleDeleteFilter: (index) => {
    index;
    return;
  },
  handleAddCriteria: () => {
    return;
  },
  tableData: initTableData(),
  handleTableSelectionChange: (selectedIds) => {
    selectedIds;
    return;
  },
  handleColumnsChange: (newColumns) => {
    newColumns;
    return;
  },
});

/**
 * @param {{children: React.ReactNode}} props
 */
export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(initSettings);

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [taskFilterFields, setTaskFilterFields] = useState([]);
  const [eventFilterFields, setEventFilterFields] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  /** @type {[FilterContainer[], React.Dispatch<React.SetStateAction<FilterContainer[]>>]} */
  const [criteria, setCriteria] = useState(initCriteria);

  /** @type {[TableData|null, React.Dispatch<React.SetStateAction<(TableData|null)>>]} */
  const [tableData, setTableData] = useState(
    /** @returns {TableData | null}  */
    () => {
      return null;
    }
  );
  const [isTableLoading, setIsTableLoading] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);

  const {
    debouncedSaveSettings,
    fetchTeamMembersData,
    handleChange,
    handleTabChange,
    handleDeleteFilter,
  } = useSettingUtil({
    settings: settings,
    setSettings: setSettings,
    setSaveSuccess: setSaveSuccess,
    setSaving: setSaving,
    setTableData: setTableData,
    setIsTableLoading: setIsTableLoading,
    setCurrentTab: setCurrentTab,
    setCriteria: setCriteria,
  });

  /** @type {() => void} */
  const handleAddCriteria = useCallback(() => {
    setCriteria((prevCriteria) => {
      const newCriteria = [
        ...prevCriteria,
        { filters: [], filterLogic: "", name: "" },
      ];
      setSettings((prev) => {
        const updatedSettings = { ...prev, criteria: newCriteria };
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
      return newCriteria;
    });
  }, [debouncedSaveSettings]);

  /** @type {(index: number, value: FilterContainer) => void} */
  const handleCriteriaChange = useCallback(
    (index, newContainer) => {
      setSettings((prev) => {
        const newCriteria = [...prev.criteria];
        newCriteria[index] = newContainer;
        const updatedSettings = { ...prev, criteria: newCriteria };
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
    },
    [debouncedSaveSettings]
  );

  /** @type {(selectedIds: Set<string>) => void} */
  const handleTableSelectionChange = useCallback(
    (selectedIds) => {
      const teamMemberIds = Array.from(selectedIds);
      setSettings((prev) => {
        const updatedSettings = {
          ...prev,
          teamMemberIds,
          userRole:
            teamMemberIds.length > 0
              ? "I manage a team"
              : "I am an individual contributor",
        };
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
      setTableData((prev) => {
        if (prev === null) {
          return null;
        }

        return {
          ...prev,
          selectedIds,
        };
      });
    },
    [debouncedSaveSettings]
  );

  /** @param {Date} date */
  const formatDateForInput = (date) => {
    if (!date) return "";

    // Parse the input date string
    const d = new Date(date);

    // Format the date components with leading zeros if necessary
    /** @param {number} num */
    const pad = (num) => (num < 10 ? "0" : "") + num;
    const year = d.getFullYear();
    const month = pad(d.getMonth() + 1);
    const day = pad(d.getDate());
    const hours = pad(d.getHours());
    const minutes = pad(d.getMinutes());

    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  /** @type {(newColumns: TableColumn[]) => void} */
  const handleColumnsChange = useCallback((newColumns) => {
    setTableData((prev) => {
      if (prev === null) {
        return null;
      }

      return {
        ...prev,
        columns: newColumns,
      };
    });
  }, []);

  return (
    <SettingsContext.Provider
      value={{
        settings,
        setSettings,
        status: {
          saving,
          saveSuccess,
          isLoading,
          isTableLoading,
          setSaving,
          setSaveSuccess,
          setIsLoading,
          setIsTableLoading,
        },
        currentTab,
        setCurrentTab,
        filter: {
          eventFilterFields,
          taskFilterFields,
          setEventFilterFields,
          setTaskFilterFields,
        },
        handleTabChange,
        criteria,
        setCriteria,
        handleChange,
        formatDateForInput,
        tableData,
        setTableData,
        fetchTeamMembersData,
        handleCriteriaChange,
        handleDeleteFilter,
        handleAddCriteria,
        handleTableSelectionChange,
        handleColumnsChange,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
};
