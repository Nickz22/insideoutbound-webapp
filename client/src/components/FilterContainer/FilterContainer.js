import React from "react";
import {
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  IconButton,
  Tooltip,
  Box,
  Button,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";

const FilterContainer = ({
  filters,
  taskFilterFields,
  FILTER_OPERATOR_MAPPING,
  onFieldChange,
  onOperatorChange,
  onValueChange,
  onDeleteFilter,
  onAddFilter,
  onLogicChange,
  filterLogic,
  logicError,
}) => {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Box sx={{ flexGrow: 1, overflowY: "auto" }}>
        {filters.map((filter, idx) => (
          <Box
            key={idx}
            sx={{
              mb: 2,
              p: 2,
              backgroundColor: "#f9f9f9",
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
                    onChange={(event) => onFieldChange(event.target.value, idx)}
                  >
                    {taskFilterFields.map((field) => (
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
                    onChange={(event) =>
                      onOperatorChange(event.target.value, idx)
                    }
                  >
                    {Object.entries(
                      FILTER_OPERATOR_MAPPING[filter.dataType] || {}
                    ).map(([key, value]) => (
                      <MenuItem key={key} value={key}>
                        {key}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={5}>
                <TextField
                  fullWidth
                  label="Value"
                  value={filter.value}
                  variant="outlined"
                  size="small"
                  onChange={(event) => onValueChange(event.target.value, idx)}
                />
              </Grid>
              <Grid item xs={12} sm={1}>
                <Tooltip title="Remove filter">
                  <IconButton
                    aria-label="delete"
                    onClick={() => onDeleteFilter(idx)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </Grid>
            </Grid>
          </Box>
        ))}
      </Box>
      <Box
        sx={{
          mt: "auto",
          pt: 2,
          borderTop: "1px solid #e0e0e0",
          backgroundColor: "white",
          position: "sticky",
          bottom: 0,
          zIndex: 1,
        }}
      >
        <TextField
          label="Logic"
          value={filterLogic}
          variant="outlined"
          fullWidth
          margin="normal"
          error={!!logicError}
          helperText={logicError}
          onChange={(event) => onLogicChange(event.target.value)}
        />
      </Box>
    </Box>
  );
};

export default FilterContainer;
