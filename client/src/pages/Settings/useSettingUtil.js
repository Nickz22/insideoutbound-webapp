import { useCallback, useMemo } from "react";
import { debounce } from "lodash";
import {
  saveSettings,
  deleteAllActivations,
  fetchSalesforceUsers
} from "src/components/Api/Api";

/** @typedef {import("types/Settings").SettingsContextValue} SettingsContextValue */
/** @typedef {import("types/FilterContainer").FilterContainer} FilterContainer */
/** @typedef {import("types/TableData").TableData} TableData */
/** @typedef {import("types/TableColumn").TableColumn} TableColumn */
/** @typedef {import("types/Settings").Settings} Settings */

/**
 * @param {Object} params
 * @param {Settings} params.settings
 * @param {React.Dispatch<React.SetStateAction<Settings>>} params.setSettings
 * @param {React.Dispatch<React.SetStateAction<TableData | null>>} params.setTableData
 * @param {React.Dispatch<React.SetStateAction<boolean>>} params.setSaving
 * @param {React.Dispatch<React.SetStateAction<boolean>>} params.setSaveSuccess
 * @param {React.Dispatch<React.SetStateAction<boolean>>} params.setIsTableLoading
 * @param {React.Dispatch<React.SetStateAction<number>>} params.setCurrentTab
 * @param {React.Dispatch<React.SetStateAction<Settings["criteria"]>>} params.setCriteria
 */
export const useSettingUtil = ({
  settings,
  setSettings,
  setTableData,
  setSaving,
  setSaveSuccess,
  setIsTableLoading,
  setCurrentTab,
  setCriteria,
}) => {
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

  const debouncedDeleteAllActivations = debounce(deleteAllActivations, 1000);

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
            debouncedDeleteAllActivations();
            break;
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [debouncedSaveSettings]
  );

  return {
    handleChange,
    fetchTeamMembersData,
    debouncedSaveSettings,
    handleTabChange,
    handleDeleteFilter,
  };
};
