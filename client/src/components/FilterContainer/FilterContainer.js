import React from "react";
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Grid,
  Tooltip,
  Typography,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import { useFilterLogic } from "./useFilterLogic";

/**
 * @typedef {import('types').FilterContainer} FilterContainer
 * @typedef {import('types').Filter} Filter
 * @typedef {import('types').CriteriaField} CriteriaField
 */

/**
 * @param {{initialFilterContainer: FilterContainer, filterFields: CriteriaField[], filterOperatorMapping: { [key: string]: {[key:string]: string} }, hasNameField: boolean, hasDirectionField: boolean, onLogicChange: Function, onValueChange: Function}} props
 * @returns
 */
const FilterContainer = ({
  initialFilterContainer,
  filterFields,
  filterOperatorMapping,
  hasNameField,
  hasDirectionField,
  onLogicChange,
  onValueChange,
}) => {
  const {
    filterContainer,
    logicErrors,
    handleFieldChange,
    handleOperatorChange,
    handleValueChange,
    handleLogicChange,
    handleAddFilter,
    handleDeleteFilter,
    handleNameChange,
  } = useFilterLogic(initialFilterContainer, filterFields);

  const handleDirectionChange = (e) => {
    const newDirection = e.target.value;
    handleValueChange("direction", newDirection, onValueChange);
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "600px", // Increased overall height
        p: 2,
        border: "1px solid #e0e0e0",
        borderRadius: "8px",
      }}
    >
      {hasNameField && (
        <TextField
          label="Name"
          value={filterContainer.name}
          onChange={(e) => handleNameChange(e.target.value)}
          variant="outlined"
          fullWidth
          margin="normal"
        />
      )}
      {hasDirectionField && (
        <Tooltip title="Inbound engagements are interactions initiated by the prospect, while outbound engagements are initiated by your team.">
          <Box mt={2} mb={1}>
            <FormControl fullWidth size="small">
              <InputLabel>Direction</InputLabel>
              <Select
                value={filterContainer.direction || ""}
                label="Direction"
                onChange={handleDirectionChange}
              >
                <MenuItem value="inbound">Inbound</MenuItem>
                <MenuItem value="outbound">Outbound</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Tooltip>
      )}
      <Typography variant="h6" gutterBottom>
        Filters
      </Typography>
      <Box sx={{ flexGrow: 1, overflowY: "auto", mb: 2, maxHeight: "400px" }}>
        {filterContainer.filters.map(
          /**
           * @param {Filter} filter
           * @param {number} index
           **/
          (filter, index) => (
            <Box
              key={index}
              sx={{
                mb: 2,
                p: 2,
                backgroundColor: "#f5f5f5",
                borderRadius: "4px",
              }}
            >
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Field</InputLabel>
                    <Select
                      value={filter.field}
                      label="Field"
                      onChange={(e) => handleFieldChange(index, e.target.value)}
                    >
                      {filterFields.map((field) => (
                        <MenuItem key={field.name} value={field.name}>
                          {field.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Operator</InputLabel>
                    <Select
                      value={filter.operator}
                      label="Operator"
                      onChange={(e) =>
                        handleOperatorChange(index, e.target.value)
                      }
                    >
                      {Object.keys(
                        filterOperatorMapping[filter.dataType] || {}
                      ).map((key) => (
                        <MenuItem key={key} value={key}>
                          {key}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={5}>
                  {filter.options?.length > 0 ? (
                    <FormControl fullWidth size="small">
                      <InputLabel>Value</InputLabel>
                      <Select
                        value={filter.value}
                        label="Value"
                        onChange={(e) =>
                          handleValueChange(
                            index,
                            e.target.value,
                            onValueChange
                          )
                        }
                      >
                        {filter.options.map((option, optionIndex) => (
                          <MenuItem key={optionIndex} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  ) : (
                    <TextField
                      fullWidth
                      label="Value"
                      value={filter.value}
                      variant="outlined"
                      size="small"
                      onChange={(e) =>
                        handleValueChange(index, e.target.value, onValueChange)
                      }
                    />
                  )}
                </Grid>
                <Grid item xs={12} sm={1}>
                  <IconButton
                    onClick={() => handleDeleteFilter(index)}
                    aria-label="delete"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Grid>
              </Grid>
            </Box>
          )
        )}
        <Button
          startIcon={<AddIcon />}
          onClick={handleAddFilter}
          variant="outlined"
          sx={{ mb: 2 }}
        >
          Add Filter
        </Button>
      </Box>
      <Box>
        <TextField
          label="Logic"
          value={filterContainer.filterLogic}
          variant="outlined"
          fullWidth
          margin="normal"
          error={!!logicErrors[0]}
          helperText={
            logicErrors[0] ||
            "Use AND, OR, and numbers to create logic (e.g., 1 AND 2 OR 3)"
          }
          onChange={(e) => handleLogicChange(e.target.value, onLogicChange)}
        />
      </Box>
    </Box>
  );
};

export default FilterContainer;
