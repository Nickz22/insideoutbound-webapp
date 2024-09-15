/**
 * Sorts the data based on the given orderBy and order parameters
 * @param {Array} data - The data to be sorted
 * @param {string} orderBy - The key to sort by
 * @param {string} order - The order of sorting ('asc' or 'desc')
 * @returns {Array} - The sorted data
 */
export const sortData = (data, orderBy, order) => {
  if (!orderBy) return data;

  return [...data].sort((a, b) => {
    const aValue = a[orderBy];
    const bValue = b[orderBy];

    // Handle falsey values
    if (!aValue && bValue) return order === "asc" ? 1 : -1;
    if (aValue && !bValue) return order === "asc" ? -1 : 1;
    if (!aValue && !bValue) return 0;

    // Normal comparison for truthy values
    if (aValue < bValue) return order === "asc" ? -1 : 1;
    if (aValue > bValue) return order === "asc" ? 1 : -1;
    return 0;
  });
};

/**
 * Filters the data based on the given search term
 * @param {Array} data - The data to be filtered
 * @param {string} searchTerm - The search term to filter by
 * @returns {Array} - The filtered data
 */
export const filterData = (data, searchTerm) => {
  return data.filter((item) => {
    return Object.values(item).some((value) => {
      if (Array.isArray(value)) {
        return value.some((arrayItem) => {
          if (typeof arrayItem === "object" && arrayItem !== null) {
            return Object.values(arrayItem).some((nestedValue) => {
              return nestedValue
                ?.toString()
                .toLowerCase()
                .includes(searchTerm.toLowerCase());
            });
          } else {
            return arrayItem
              ?.toString()
              .toLowerCase()
              .includes(searchTerm.toLowerCase());
          }
        });
      } else if (typeof value === "object" && value !== null) {
        return Object.values(value).some((nestedValue) => {
          return nestedValue
            ?.toString()
            .toLowerCase()
            .includes(searchTerm.toLowerCase());
        });
      } else {
        return value
          ?.toString()
          .toLowerCase()
          .includes(searchTerm.toLowerCase());
      }
    });
  });
};
