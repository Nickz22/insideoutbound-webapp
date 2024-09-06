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
  styled,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import { useFilterLogic } from "./useFilterLogic";

/**
 * @typedef {import('types').FilterContainer} FilterContainer
 * @typedef {import('types').Filter} Filter
 * @typedef {import('types').CriteriaField} CriteriaField
 */

const StyledTextField = styled(TextField)({

  '& .MuiInput-underline:before': {
    borderBottomColor: '#533AF3', // Blue underline
  },
  '& .MuiInput-underline:hover:not(.Mui-disabled):before': {
    borderBottomColor: '#533AF3', // Blue underline on hover
  },
  '& .MuiInput-underline:after': {
    borderBottomColor: '#533AF3', // Blue underline after focus
  },
  "& input": {
    color: "rgba(83, 58, 243, 1)",
    fontWeight: "400",
    fontSize: "18px",
  }

});

/**
 * @param {{
 * initialFilterContainer: FilterContainer,
 * filterFields: CriteriaField[],
 * filterOperatorMapping: { [key: string]: {[key:string]: string} },
 * hasNameField: boolean,
 * isNameReadOnly: boolean,
 * hasDirectionField: boolean,
 * onLogicChange: Function,
 * onValueChange: Function}} props
 * @returns
 */
const FilterContainer = ({
  initialFilterContainer,
  filterFields,
  filterOperatorMapping,
  hasNameField,
  isNameReadOnly,
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
          InputProps={{
            readOnly: isNameReadOnly,
          }}
        />
      )}
      {hasDirectionField && (
        <Tooltip title="Inbound engagements are interactions initiated by the prospect, while outbound engagements are initiated by your team.">
          <Box mt={2} mb={1}>
            <FormControl fullWidth size="small">
              <InputLabel>Direction</InputLabel>
              <Select
                value={filterContainer.direction?.toLowerCase() || ""}
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
                backgroundColor: "rgba(255, 125, 47, 0.07)",
                borderRadius: "4px",
              }}
            >
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel
                      sx={{
                        fontSize: "16px",
                        color: "#4C4C4C",
                        fontWeight: "500",
                        margin: 0,
                        left: "-14px",
                        top: "4px"
                      }}
                    >FIELD</InputLabel>
                    <Select
                      value={filter.field}
                      label="FIELD"
                      onChange={(e) => handleFieldChange(index, e.target.value)}
                      variant="standard"
                      sx={{
                        color: "rgba(83, 58, 243, 1)",
                        fontWeight: "400",
                        fontSize: "18px",
                        borderBottom: "1px solid rgba(83, 58, 243, 1)",
                        "::before": {
                          borderBottom: "none"
                        },
                        "::after": {
                          borderBottom: "none"
                        },
                        ":hover": {
                          borderBottom: "2px solid rgba(83, 58, 243, 1)",
                        },
                        ":hover:not(.Mui-disabled, .Mui-error):before": {
                          borderBottom: "2px solid rgba(83, 58, 243, 1)",
                        },
                        ":hover::after": {
                          borderBottom: "none",
                        }
                      }}
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
                    <InputLabel
                      sx={{
                        fontSize: "16px",
                        color: "#4C4C4C",
                        fontWeight: "500",
                        margin: 0,
                        left: "-14px",
                        top: "4px"
                      }}
                    >OPERATOR</InputLabel>
                    <Select
                      value={filter.operator}
                      label="OPERATOR"
                      onChange={(e) =>
                        handleOperatorChange(index, e.target.value)
                      }
                      variant="standard"
                      sx={{
                        color: "rgba(83, 58, 243, 1)",
                        fontWeight: "400",
                        fontSize: "18px",
                        borderBottom: "1px solid rgba(83, 58, 243, 1)",
                        "::before": {
                          borderBottom: "none"
                        },
                        "::after": {
                          borderBottom: "none"
                        },
                        ":hover": {
                          borderBottom: "2px solid rgba(83, 58, 243, 1)",
                        },
                        ":hover:not(.Mui-disabled, .Mui-error):before": {
                          borderBottom: "2px solid rgba(83, 58, 243, 1)",
                        },
                        ":hover::after": {
                          borderBottom: "none",
                        }
                      }}
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
                      <InputLabel
                        sx={{
                          fontSize: "16px",
                          color: "#4C4C4C",
                          fontWeight: "500",
                          margin: 0,
                          left: "-14px",
                          top: "4px"
                        }}
                      >VALUE</InputLabel>
                      <Select
                        value={filter.value}
                        label="VALUE"
                        onChange={(e) =>
                          handleValueChange(
                            index,
                            e.target.value,
                            onValueChange
                          )
                        }
                        sx={{
                          color: "rgba(83, 58, 243, 1)",
                          fontWeight: "400",
                          fontSize: "18px",
                          borderBottom: "1px solid rgba(83, 58, 243, 1)",
                          "::before": {
                            borderBottom: "none"
                          },
                          "::after": {
                            borderBottom: "none"
                          },
                          ":hover": {
                            borderBottom: "2px solid rgba(83, 58, 243, 1)",
                          },
                          ":hover:not(.Mui-disabled, .Mui-error):before": {
                            borderBottom: "2px solid rgba(83, 58, 243, 1)",
                          },
                          ":hover::after": {
                            borderBottom: "none",
                          }
                        }}
                        variant="standard"
                      >
                        {filter.options.map((option, optionIndex) => (
                          <MenuItem key={optionIndex} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  ) : (
                    <StyledTextField
                      fullWidth
                      label="VALUE"
                      value={filter.value}
                      variant="standard"
                      size="small"
                      onChange={(e) =>
                        handleValueChange(index, e.target.value, onValueChange)
                      }
                      sx={{
                        color: "rgba(83, 58, 243, 1)",
                        fontWeight: "400",
                        fontSize: "18px",
                      }}
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
          sx={{
            mb: 2,
            backgroundColor: "rgba(73, 30, 255, 0.07)",
            border: "1px solid rgba(83, 58, 243, 0.27)",
            color: "#533AF3",
            width: "180px"
          }}
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
