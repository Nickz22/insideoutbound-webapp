import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Typography,
  OutlinedInput,
  InputLabel,
  FormControl,
} from "@mui/material";
import FilterListIcon from "@mui/icons-material/FilterList";
import CloseIcon from "@mui/icons-material/Close";
import CancelIcon from "@mui/icons-material/Cancel";

const DataFilter = ({ onFilter, rawData }) => {
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({
    activatedBy: [],
    accountOwner: [],
    activatedByTeam: [],
  });
  const [tempFilters, setTempFilters] = useState(filters);

  useEffect(() => {
    const initialFilters = {
      activatedBy: [],
      accountOwner: [],
      activatedByTeam: [],
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
      activatedBy: [],
      accountOwner: [],
      activatedByTeam: [],
    };
    setTempFilters(clearedFilters);
    setFilters(clearedFilters);
    onFilter(clearedFilters);
    setOpen(false);
  };

  const handleDeleteChip = (filterKey, valueToDelete) => {
    setTempFilters((prev) => ({
      ...prev,
      [filterKey]: prev[filterKey].filter((value) => value !== valueToDelete),
    }));
  };

  const uniqueActivatedBy = Array.from(
    new Set(rawData.map((item) => item.activated_by_id))
  ).map((id) => {
    const item = rawData.find((data) => data.activated_by_id === id);
    return {
      id: item.activated_by_id,
      name: `${item.activated_by.firstName} ${item.activated_by.lastName}`,
    };
  });

  const uniqueAccountOwners = [
    ...new Map(
      rawData.map((item) => [
        item?.account?.owner?.id,
        {
          id: item?.account?.owner?.id,
          name: `${item?.account?.owner?.firstName || ''} ${item?.account?.owner?.lastName || ''}`.trim() || 'Unknown',
        },
      ]).filter(([id]) => id != null)
    ).values(),
  ];

  const uniqueActivatedByTeams = [
    ...new Set(rawData.map((item) => item.activated_by.role)),
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
        {Object.values(filters).some((v) => v.length > 0) && (
          <Chip
            label={Object.values(filters).filter((v) => v.length > 0).length}
            size="small"
            color="primary"
            sx={{ ml: 1 }}
          />
        )}
      </Button>
      <Box
        sx={{
          position: "fixed",
          left: open ? "240px" : "-25%", // 240px is sidebar width
          top: 0,
          width: "25%",
          height: "100%",
          bgcolor: "background.paper",
          boxShadow: 3,
          p: 4,
          transition: "left 0.3s ease-in-out",
          overflowY: "auto",
          zIndex: 10
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
          <FormControl fullWidth>
            <InputLabel id="activated-by-label">Activated By</InputLabel>
            <Select
              labelId="activated-by-label"
              multiple
              value={tempFilters.activatedBy}
              onChange={(e) =>
                handleFilterChange("activatedBy", e.target.value)
              }
              input={<OutlinedInput label="Activated By" />}
              renderValue={(selected) => (
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip
                      key={value}
                      label={
                        uniqueActivatedBy.find((u) => u.id === value)?.name
                      }
                      onDelete={() => handleDeleteChip("activatedBy", value)}
                      deleteIcon={
                        <CancelIcon
                          onMouseDown={(event) => event.stopPropagation()}
                        />
                      }
                    />
                  ))}
                </Box>
              )}
              displayEmpty
            >
              {uniqueActivatedBy.map((user) => (
                <MenuItem key={user.id} value={user.id}>
                  {user.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel id="account-owner-label">Account Owner</InputLabel>
            <Select
              labelId="account-owner-label"
              multiple
              value={tempFilters.accountOwner}
              onChange={(e) =>
                handleFilterChange("accountOwner", e.target.value)
              }
              input={<OutlinedInput label="Account Owner" />}
              renderValue={(selected) => (
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip
                      key={value}
                      label={
                        uniqueAccountOwners.find((o) => o.id === value)?.name
                      }
                      onDelete={() => handleDeleteChip("accountOwner", value)}
                      deleteIcon={
                        <CancelIcon
                          onMouseDown={(event) => event.stopPropagation()}
                        />
                      }
                    />
                  ))}
                </Box>
              )}
              displayEmpty
            >
              {uniqueAccountOwners.map((owner) => (
                <MenuItem key={owner.id} value={owner.id}>
                  {owner.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel id="activated-by-team-label">
              Activated By Team
            </InputLabel>
            <Select
              labelId="activated-by-team-label"
              multiple
              value={tempFilters.activatedByTeam}
              onChange={(e) =>
                handleFilterChange("activatedByTeam", e.target.value)
              }
              input={<OutlinedInput label="Activated By Team" />}
              renderValue={(selected) => (
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip
                      key={value}
                      label={value}
                      onDelete={() =>
                        handleDeleteChip("activatedByTeam", value)
                      }
                      deleteIcon={
                        <CancelIcon
                          onMouseDown={(event) => event.stopPropagation()}
                        />
                      }
                    />
                  ))}
                </Box>
              )}
              displayEmpty
            >
              {uniqueActivatedByTeams.map((team) => (
                <MenuItem key={team} value={team}>
                  {team}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

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
