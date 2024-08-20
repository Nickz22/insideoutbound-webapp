import { debounce } from "lodash";
import {
    createContext,
    useCallback,
    useContext,
    useMemo,
    useState,
} from "react";
import { deleteAllActivations, fetchSalesforceUsers, saveSettings } from "src/components/Api/Api";

/** @typedef {import("types/Settings").SettingsContextValue} SettingsContextValue */
/** @typedef {import("types/FilterContainer").FilterContainer} FilterContainer */
/** @typedef {import("types/TableData").TableData} TableData */
/** @typedef {import("types/TableColumn").TableColumn} TableColumn */

/** @type {FilterContainer} */
const initMeetingsCriteria = { filters: [], filterLogic: "", name: "" }

/** @type {FilterContainer[]} */
const initCriteria = []

/** @type {string[]} */
const initTeamMemberIds = []

/** @type {any[]} */
const initEventFilterFields = []

/** @type {any[]} */
const initTaskFilterFields = []

/** @returns {TableData | null}  */
const initTableData = () => {
    return null;
}

/** @type {import("react").Context<SettingsContextValue>} */
const SettingsContext = createContext({
    settings: {
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
    },
    criteria: initCriteria,
    status: {
        isLoading: Boolean(false),
        isTableLoading: Boolean(false),
        saveSuccess: Boolean(false),
        saving: Boolean(false)
    },
    currentTab: 0,
    filter: {
        eventFilterFields: initEventFilterFields,
        taskFilterFields: initTaskFilterFields
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
    fetchTeamMembersData: async (selectedIds) => { selectedIds; return; },
    handleDeleteFilter: (index) => { index; return; },
    handleAddCriteria: () => { return; },
    tableData: initTableData(),
    handleTableSelectionChange: (selectedIds) => { selectedIds; return; },
    handleColumnsChange: (newColumns) => { newColumns; return; }
});

/**
 * @param {{children: React.ReactNode}} props
 */
export const SettingsProvider = ({
    children,
}) => {
    const [settings, setSettings] = useState({
        inactivityThreshold: 0,
        criteria: initCriteria,
        meetingObject: "",
        meetingsCriteria: { filters: [], filterLogic: "", name: "" },
        activitiesPerContact: 0,
        contactsPerAccount: 0,
        trackingPeriod: 0,
        activateByMeeting: false,
        activateByOpportunity: false,
        userRole: "",
        teamMemberIds: initTeamMemberIds,
        latestDateQueried: null,
    });

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

    const debouncedSaveSettings = useMemo(
        () =>
            debounce(async (settings) => {
                const { userRole, ...settingsToSave } = settings;
                setSaving(true);
                try {
                    saveSettings(settingsToSave);
                    setSaveSuccess(true);
                } catch (error) {
                    console.error("Error saving settings:", error);
                } finally {
                    setSaving(false);
                }
            }, 500),
        []
    );

    /** @type {(field: string, value: string | number | boolean | FilterContainer) => void} */
    const handleChange = useCallback(
        (field, value) => {
            setSettings((prev) => {
                const updatedSettings = { ...prev, [field]: value };

                switch (field) {
                    case "userRole":
                        if (value === "I manage a team") {
                            fetchTeamMembersData(prev.teamMemberIds);
                        } else {
                            setTableData(null);
                            updatedSettings.teamMemberIds = [];
                        }
                        break;
                    case "meetingObject":
                        if (value !== settings.meetingObject) {
                            updatedSettings.meetingsCriteria = {
                                filters: [],
                                filterLogic: "",
                                name: "",
                            };
                        }
                        break;
                    case "latestDateQueried":
                        deleteAllActivations();
                }

                debouncedSaveSettings(updatedSettings);
                return updatedSettings;
            });
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [debouncedSaveSettings]
    );

    /** @type {import("@mui/material").TabsOwnProps["onChange"]} */
    const handleTabChange = (event, newValue) => {
        setCurrentTab(newValue);
        // Scroll to the corresponding section
        const sectionId = ["general", "prospecting", "meeting", "user-role"][
            newValue
        ];
        const element = document.getElementById(sectionId);
        if (element) {
            element.scrollIntoView({ behavior: "smooth" });
        }
    };

    /** @param {string[]} selectedIds */
    const fetchTeamMembersData = async (selectedIds = []) => {
        setIsTableLoading(true);
        try {
            const response = await fetchSalesforceUsers();
            if (response.success) {
                /** @type {TableColumn[]} */
                const columns = [
                    { id: "select", label: "Select", dataType: "select" },
                    { id: "photoUrl", label: "", dataType: "image" },
                    { id: "firstName", label: "First Name", dataType: "string" },
                    { id: "lastName", label: "Last Name", dataType: "string" },
                    { id: "email", label: "Email", dataType: "string" },
                    { id: "role", label: "Role", dataType: "string" },
                    { id: "username", label: "Username", dataType: "string" },
                ];
                setTableData({
                    columns,
                    data: response.data,
                    selectedIds: new Set(selectedIds),
                    availableColumns: columns,
                });
            } else {
                console.error("Error fetching Salesforce users:", response.message);
            }
        } catch (error) {
            console.error("Error fetching Salesforce users:", error);
        } finally {
            setIsTableLoading(false);
        }
    };

    /** @type {(index: number) => void} */
    const handleDeleteFilter = useCallback(
        (index) => {
            setCriteria((prevCriteria) => {
                const newCriteria = prevCriteria.filter((_, i) => i !== index);
                setSettings((prev) => {
                    const updatedSettings = { ...prev, criteria: newCriteria };
                    debouncedSaveSettings(updatedSettings);
                    return updatedSettings;
                });
                return newCriteria;
            });
        },
        [debouncedSaveSettings]
    );

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

        // Parse the input date string and get the date in UTC
        const d = new Date(date);

        // Format the date components with leading zeros if necessary

        /** @param {number} num */
        const pad = (num) => (num < 10 ? "0" : "") + num;
        const year = d.getUTCFullYear();
        const month = pad(d.getUTCMonth() + 1);
        const day = pad(d.getUTCDate());
        const hours = pad(d.getUTCHours());
        const minutes = pad(d.getUTCMinutes());

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
                    setTaskFilterFields
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
                handleColumnsChange
            }}
        >
            {children}
        </SettingsContext.Provider>
    );
};

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (!context) {
        throw new Error(
            "useSettings must be used within a SettingsProvider"
        );
    }
    return context;
};
