import React, { useState } from "react";
import {
  Box,
  Select,
  MenuItem,
  TextField,
  Button,
  Tooltip,
} from "@mui/material";

const DataFilter = ({ fields, onFilter, onClear }) => {
  const [selectedField, setSelectedField] = useState("");
  const [operator, setOperator] = useState("equals");
  const [filterValue, setFilterValue] = useState("");

  const handleApplyFilter = () => {
    onFilter({ field: selectedField, operator, value: filterValue });
  };

  const handleClearFilter = () => {
    setSelectedField("");
    setOperator("equals");
    setFilterValue("");
    onClear();
  };

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Tooltip
        title="Filter on Activation Account fields"
        arrow
        placement="top"
      >
        <Select
          value={selectedField}
          onChange={(e) => setSelectedField(e.target.value)}
          displayEmpty
          size="small"
          sx={{ minWidth: 120 }}
        >
          <MenuItem value="" disabled>
            Select Field
          </MenuItem>
          {fields.map((field) => (
            <MenuItem key={field} value={field}>
              {field}
            </MenuItem>
          ))}
        </Select>
      </Tooltip>
      <Select
        value={operator}
        onChange={(e) => setOperator(e.target.value)}
        size="small"
        sx={{ minWidth: 100 }}
      >
        <MenuItem value="equals">Equals</MenuItem>
        <MenuItem value="notEquals">Does Not Equal</MenuItem>
      </Select>
      <TextField
        placeholder="Filter Value"
        value={filterValue}
        onChange={(e) => setFilterValue(e.target.value)}
        size="small"
        sx={{ width: 150 }}
      />
      <Button onClick={handleApplyFilter} variant="contained" size="small">
        Apply
      </Button>
      {filterValue && (
        <Button onClick={handleClearFilter} variant="outlined" size="small">
          Clear
        </Button>
      )}
    </Box>
  );
};

export default DataFilter;
