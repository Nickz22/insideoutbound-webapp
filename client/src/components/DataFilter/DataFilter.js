import React, { useState } from "react";
import {
  Box,
  TextField,
  Button,
} from "@mui/material";
import CustomSelect from "../CustomSelect/CustomSelect";

/**
 * @param {object} props
 * @param {any} props.fields
 * @param {any} props.onFilter
 * @param {any} props.onClear
 */
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
    <Box sx={{ display: "flex", alignItems: "center", gap: "25px" }}>
      <CustomSelect
        tooltip={{ title: "Filter on Activation Account fields", arrow: true, placement: "bottom" }}
        key={"Filter activation"}
        value={selectedField}
        onChange={(e) => setSelectedField(e.target.value)}
        options={fields}
        placeholder="Select Field"
        selectSx={{
          width: "125px",
          fontSize: "16px",
          lineHeight: "1.78",
          letterSpacing: "-0.48px",
        }}
      />

      <CustomSelect
        value={operator}
        onChange={(e) => setOperator(e.target.value)}
        placeholder="Select Field"
        selectSx={{
          width: "100px",
          fontSize: "16px",
          lineHeight: "1.78",
          letterSpacing: "-0.48px",
        }}
        options={[
          { value: "equals", label: "Equals" },
          { value: "notEquals", label: "Does Not Equal" },
        ]}
      />

      <Box sx={{ display: "flex", alignItems: "center", gap: "9px" }}>
        <TextField
          placeholder="Filter Value"
          value={filterValue}
          onChange={(e) => setFilterValue(e.target.value)}
          size="small"
          sx={{
            width: "177px",
            height: "38px",
            '& .MuiInputBase-input': {
              boxSizing: "border-box",
              height: "38px",
              fontSize: '13px',
              lineHeight: "1.78",
              fontWeight: "500",
              color: "#4C4C4C",
              '&:hover': {
                borderColor: "rgba(83, 58, 243, 1)"
              },
              '&::placeholder': {
                color: "#4C4C4C",
                opacity: 1
              }
            },
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: "#E9E9E9", // Normal border color
              },
              '&:hover fieldset': {
                borderColor: "rgba(83, 58, 243, 1)", // Hover border color
              }
            }
          }}
        />
        <Button
          onClick={handleApplyFilter}
          variant="contained"
          size="small"
          sx={{
            width: "96px",
            padding: "4px 10px",
            height: "38px",
            boxSizing: "border-box",
            backgroundColor: "#F3F0FE",
            color: "#533AF3",
            fontSize: "16px",
            fontWeight: 600,
            lineHeight: "1.78",
            letterSpacing: "0.64px",
            border: "1px solid rgba(83, 58, 243, 0.27)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            boxShadow: "none",
            '&:hover': {
              boxShadow: "none",
              backgroundColor: "#E0DCF5",
              borderColor: "rgba(83, 58, 243, 0.4)"
            }
          }}
        >
          Apply
        </Button>
        {filterValue && (
          <Button
            onClick={handleClearFilter}
            variant="outlined"
            size="small"
            sx={{
              width: "96px",
              height: "38px",
              fontSize: "16px",
              fontWeight: 600,
              lineHeight: "1.78",
              letterSpacing: "0.64px",
              padding: "4px 10px",
              boxSizing: "border-box",
              borderColor: "#F3F0FE",
              color: "#533AF3",
              '& .MuiButton-outlined': {
                borderColor: "#F3F0FE"
              },
              '&:hover': {
                backgroundColor: "#533AF3",
                color: "#FFFFFF"
              },
            }}
          >
            Clear
          </Button>
        )}
      </Box>
    </Box>
  );
};

export default DataFilter;
