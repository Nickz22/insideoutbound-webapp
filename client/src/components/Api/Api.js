import axios from "axios";

export const fetchTaskFilterFields = async () => {
  return await axios.get("http://localhost:8000/get_task_criteria_fields", {
    validateStatus: () => true,
  });
};

export const fetchEventFilterFields = async () => {
  return await axios.get("http://localhost:8000/get_event_criteria_fields", {
    validateStatus: () => true,
  });
};
