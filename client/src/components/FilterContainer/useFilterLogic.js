import { useState, useCallback } from "react";

export const useFilterLogic = (initialFilterContainer, filterFields) => {
  const [filterContainer, setFilterContainer] = useState(
    initialFilterContainer || {
      filterLogic: "",
      filters: [],
      name: "",
    }
  );
  const [logicErrors, setLogicErrors] = useState({});

  const handleFieldChange = useCallback(
    (filterIndex, value) => {
      setFilterContainer((prevContainer) => {
        const newFilters = [...prevContainer.filters];
        newFilters[filterIndex] = {
          ...newFilters[filterIndex],
          field: value,
          value: "",
          operator: "",
          dataType:
            filterFields.find((field) => field.name === value)?.type ||
            "string",
        };
        return { ...prevContainer, filters: newFilters };
      });
    },
    [filterFields]
  );

  const handleOperatorChange = useCallback((filterIndex, value) => {
    setFilterContainer((prevContainer) => {
      const newFilters = [...prevContainer.filters];
      newFilters[filterIndex] = { ...newFilters[filterIndex], operator: value };
      return { ...prevContainer, filters: newFilters };
    });
  }, []);

  const handleValueChange = useCallback((filterIndex, value, onValueChange) => {
    setFilterContainer((prevContainer) => {
      const newFilters = [...prevContainer.filters];
      newFilters[filterIndex] = { ...newFilters[filterIndex], value: value };
      if (onValueChange) {
        onValueChange({ ...prevContainer, filters: newFilters });
      }
      return { ...prevContainer, filters: newFilters };
    });
  }, []);

  const handleLogicChange = useCallback(
    (value, onLogicChange) => {
      const error = validateFilterLogic(filterContainer.filters, value);
      const newFilterContainer = { ...filterContainer, filterLogic: value };
      setFilterContainer((prevContainer) => newFilterContainer);
      setLogicErrors({ 0: error });
      if (!error && onLogicChange) {
        onLogicChange(newFilterContainer);
      }
    },
    [filterContainer.filters]
  );

  const handleAddFilter = useCallback(() => {
    setFilterContainer((prevContainer) => ({
      ...(prevContainer
        ? prevContainer
        : { filters: [], filterLogic: "", name: "" }),
      filters: [
        ...prevContainer.filters,
        { field: "", operator: "", value: "", dataType: "string" },
      ],
    }));
  }, []);

  const handleDeleteFilter = useCallback((filterIndex) => {
    setFilterContainer((prevContainer) => ({
      ...prevContainer,
      filters: prevContainer.filters.filter(
        (_, index) => index !== filterIndex
      ),
    }));
    setLogicErrors((currentErrors) => ({
      ...currentErrors,
      0: "Filter deleted. Please review and update the logic.",
    }));
  }, []);

  const handleNameChange = useCallback((value) => {
    setFilterContainer((prevContainer) => ({
      ...prevContainer,
      name: value,
    }));
  }, []);

  const validateFilterLogic = (filters, logicInput) => {
    const numberOfFilters = filters.length;
    const logicInputNumbers = logicInput.match(/\d+/g) || [];

    for (let number of logicInputNumbers) {
      if (parseInt(number, 10) > numberOfFilters) {
        return `Error: Logic input contains a number (${number}) greater than the number of filters (${numberOfFilters}).`;
      }
    }
    return null;
  };

  return {
    filterContainer,
    logicErrors,
    handleFieldChange,
    handleOperatorChange,
    handleValueChange,
    handleLogicChange,
    handleAddFilter,
    handleDeleteFilter,
    handleNameChange,
  };
};
