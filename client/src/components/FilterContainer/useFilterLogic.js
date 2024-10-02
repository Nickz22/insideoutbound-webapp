import { useState, useEffect, useCallback } from "react";

/**
 * @typedef {import('types').FilterContainer} FilterContainer
 * @typedef {import('types').CriteriaField} CriteriaField
 * @typedef {import('types').Filter} Filter
 */

/**
 *
 * @param {FilterContainer} initialFilterContainer
 * @param {CriteriaField[]} filterFields
 * @returns
 */
export const useFilterLogic = (initialFilterContainer, initialFilterFields) => {
  const [filterContainer, setFilterContainer] = useState({
    ...initialFilterContainer,
  });

  const [filterFields, setFilterFields] = useState(initialFilterFields);

  useEffect(() => {
    setFilterContainer(initialFilterContainer);
  }, [initialFilterContainer]);

  useEffect(() => {
    setFilterFields(initialFilterFields);
  }, [initialFilterFields]);

  /** @type {[{[key: number]: any}, Function]} */
  const [logicErrors, setLogicErrors] = useState({});

  const handleFieldChange = useCallback(
    (filterIndex, value) => {
      setFilterContainer((prevContainer) => {
        const newFilters = [...prevContainer.filters];
        const selectedField = filterFields.find(
          (field) => field.name === value
        );
        newFilters[filterIndex] = {
          ...newFilters[filterIndex],
          field: value,
          value: "",
          operator: "",
          dataType: selectedField?.type || "string",
          options: selectedField?.options || undefined,
        };
        return { ...prevContainer, filters: newFilters };
      });
    },
    [filterFields]
  );

  const handleOperatorChange = useCallback(
    /**
     * @param {number} filterIndex
     * @param {any} value
     */
    (filterIndex, value) => {
      setFilterContainer((prevContainer) => {
        const newFilters = [...prevContainer.filters];
        newFilters[filterIndex] = {
          ...newFilters[filterIndex],
          operator: value,
        };
        return { ...prevContainer, filters: newFilters };
      });
    },
    []
  );

  const handleValueChange = useCallback(
    /**
     *
     * @param {number|string} filterIndexOrField
     * @param {any} value
     * @param {Function} onValueChange
     */
    (filterIndexOrField, value, onValueChange) => {
      setFilterContainer((prevContainer) => {
        if (typeof filterIndexOrField === "string") {
          const newContainer = {
            ...prevContainer,
            [filterIndexOrField]: value,
          };
          if (onValueChange) {
            onValueChange(newContainer);
          }
          return newContainer;
        } else {
          const newFilters = [...prevContainer.filters];
          newFilters[filterIndexOrField] = {
            ...newFilters[filterIndexOrField],
            value: value,
          };
          const newContainer = { ...prevContainer, filters: newFilters };
          if (onValueChange) {
            onValueChange(newContainer);
          }
          return newContainer;
        }
      });
    },
    []
  );

  const handleLogicChange = useCallback(
    /**
     * @param {any} value
     * @param {Function} onLogicChange
     */
    (value, onLogicChange) => {
      const error = validateFilterLogic(filterContainer.filters, value);
      const newFilterContainer = { ...filterContainer, filterLogic: value };
      setFilterContainer(() => newFilterContainer);
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
        : { filters: [], filterLogic: "", name: "", direction: "" }),
      filters: [
        ...prevContainer.filters,
        { field: "", operator: "", value: "", dataType: "string" },
      ],
      filterLogic: prevContainer.filters.length === 0 ? "1" : `${prevContainer.filterLogic} AND ${prevContainer.filters.length + 1}`
    }));
  }, []);

  const handleDeleteFilter = useCallback(
    /**
     * @param {number} filterIndex
     */
    (filterIndex) => {
      setFilterContainer((prevContainer) => ({
        ...prevContainer,
        filters: prevContainer.filters.filter(
          (_, index) => index !== filterIndex
        ),
      }));
      setLogicErrors(
        /**
         * @param {{[key: number]: any}} currentErrors
         */
        (currentErrors) => ({
          ...currentErrors,
          0: "Filter deleted. Please review and update the logic.",
        })
      );
    },
    []
  );

  const handleNameChange = useCallback(
    /**
     * @param {any} value
     */
    (value) => {
      setFilterContainer((prevContainer) => ({
        ...prevContainer,
        name: value,
      }));
    },
    []
  );

  /**
   *
   * @param {Filter[]} filters
   * @param {string} logicInput
   * @returns
   */
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
