import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  Slider,
  TextField,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Typography,
} from "@mui/material";
import FilterListIcon from "@mui/icons-material/FilterList";
import CloseIcon from "@mui/icons-material/Close";

const DataFilter = ({ onFilter, rawData }) => {
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({
    industry: [],
    annualRevenue: [0, 1000000],
    activatedBy: "",
    employeeCount: [0, 1000],
    createdDate: { start: "", end: "" },
  });
  const [tempFilters, setTempFilters] = useState(filters);

  useEffect(() => {
    const initialFilters = {
      industry: [], // This should be an empty array, not all industries
      annualRevenue: [0, 1000000],
      activatedBy: "",
      employeeCount: [0, 1000],
      createdDate: { start: "", end: "" },
    };

    setFilters(initialFilters);
    setTempFilters(initialFilters);
  }, [rawData]);

  const handleFilterChange = (key, value) => {
    setTempFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleApplyFilters = () => {
    setFilters(tempFilters);
    onFilter(tempFilters);
    setOpen(false);
  };

  const handleClearFilters = () => {
    const clearedFilters = {
      industry: [],
      annualRevenue: [0, 100000000],
      activatedBy: "",
      employeeCount: [0, 100000],
      createdDate: { start: "", end: "" },
    };
    setTempFilters(clearedFilters);
    setFilters(clearedFilters);
    onFilter(clearedFilters);
    setOpen(false);
  };

  const uniqueIndustries = [
    ...new Set(rawData.map((item) => item.account.industry)),
  ];
  const uniqueActivatedBy = [
    ...new Map(
      rawData.map((item) => [
        item.activated_by_id,
        {
          id: item.activated_by_id,
          name: `${item.activated_by.firstName} ${item.activated_by.lastName}`,
        },
      ])
    ).values(),
  ];

  return (
    <Box>
      <Button
        startIcon={<FilterListIcon />}
        onClick={() => setOpen(!open)}
        variant="text"
        sx={{ color: "blue" }}
      >
        Filters
        {Object.values(filters).some((v) => v.length || v !== "") && (
          <Chip
            label={
              Object.values(filters).filter((v) => v.length || v !== "").length
            }
            size="small"
            color="primary"
            sx={{ ml: 1 }}
          />
        )}
      </Button>
      <Box
        sx={{
          position: "fixed",
          left: open ? "12%" : "-25%",
          top: 0,
          width: "25%",
          height: "100%",
          bgcolor: "background.paper",
          boxShadow: 3,
          p: 4,
          transition: "left 0.3s ease-in-out",
          overflowY: "auto",
        }}
      >
        <IconButton
          sx={{ position: "absolute", right: 8, top: 8 }}
          onClick={() => setOpen(false)}
        >
          <CloseIcon />
        </IconButton>
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Select
            multiple
            value={tempFilters.industry}
            onChange={(e) => handleFilterChange("industry", e.target.value)}
            renderValue={(selected) =>
              selected.length === 0 ? "Select Industries" : selected.join(", ")
            }
            displayEmpty
            fullWidth
          >
            <MenuItem disabled value="">
              <em>Select Industries</em>
            </MenuItem>
            {uniqueIndustries.map((ind) => (
              <MenuItem key={ind} value={ind}>
                {ind}
              </MenuItem>
            ))}
          </Select>
          <Box>
            <Typography gutterBottom>Annual Revenue</Typography>
            <Slider
              value={tempFilters.annualRevenue}
              onChange={(_, newValue) =>
                handleFilterChange("annualRevenue", newValue)
              }
              valueLabelDisplay="auto"
              min={0}
              max={1000000}
              step={10000}
            />
          </Box>
          <Select
            value={tempFilters.activatedBy}
            onChange={(e) => handleFilterChange("activatedBy", e.target.value)}
            displayEmpty
            fullWidth
          >
            <MenuItem value="">
              <em>Any Activated By</em>
            </MenuItem>
            {uniqueActivatedBy.map((user) => (
              <MenuItem key={user.id} value={user.id}>
                {user.name}
              </MenuItem>
            ))}
          </Select>
          <Box>
            <Typography gutterBottom>Employee Count</Typography>
            <Slider
              value={tempFilters.employeeCount}
              onChange={(_, newValue) =>
                handleFilterChange("employeeCount", newValue)
              }
              valueLabelDisplay="auto"
              min={0}
              max={1000}
            />
          </Box>
          <TextField
            label="Created After"
            type="date"
            value={tempFilters.createdDate.start}
            onChange={(e) =>
              handleFilterChange("createdDate", {
                ...tempFilters.createdDate,
                start: e.target.value,
              })
            }
            fullWidth
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Created Before"
            type="date"
            value={tempFilters.createdDate.end}
            onChange={(e) =>
              handleFilterChange("createdDate", {
                ...tempFilters.createdDate,
                end: e.target.value,
              })
            }
            fullWidth
            InputLabelProps={{ shrink: true }}
          />
          <Box sx={{ display: "flex", justifyContent: "space-between", mt: 2 }}>
            <Button onClick={handleClearFilters} color="secondary">
              Clear Filters
            </Button>
            <Button
              onClick={handleApplyFilters}
              variant="contained"
              color="primary"
            >
              Apply Filters
            </Button>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default DataFilter;
