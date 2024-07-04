import React, { useState, useMemo } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Checkbox,
  Paper,
  TableContainer,
  Avatar,
  TextField,
  InputAdornment,
  IconButton,
  Box,
  TablePagination,
  TableSortLabel,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";

/**
 * * @typedef {import('types').TableData} TableData
 * @typedef {import('types').TableColumn} TableColumn
 */

/**
 * @param {{ tableData: TableData, onToggle: Function, paginate?: boolean }} props
 */
const CustomTable = ({ tableData, onToggle, paginate = false }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [orderBy, setOrderBy] = useState("");
  const [order, setOrder] = useState("asc");

  const filteredData = useMemo(() => {
    return tableData.data.filter((item) =>
      Object.values(item).some((value) =>
        value?.toString()?.toLowerCase()?.includes(searchTerm?.toLowerCase())
      )
    );
  }, [tableData.data, searchTerm]);

  const sortedData = useMemo(() => {
    if (!orderBy) return filteredData;

    return [...filteredData].sort((a, b) => {
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
  }, [filteredData, orderBy, order]);

  const paginatedData = useMemo(() => {
    if (!paginate) return sortedData;
    const startIndex = page * rowsPerPage;
    return sortedData.slice(startIndex, startIndex + rowsPerPage);
  }, [sortedData, page, rowsPerPage, paginate]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSort = (columnId) => {
    const isAsc = orderBy === columnId && order === "asc";
    setOrder(isAsc ? "desc" : "asc");
    setOrderBy(columnId);
  };

  /**
   * Renders a cell based on the column data type
   * @param {TableColumn} column
   * @param {TableData} item
   * @returns {React.ReactNode}
   */
  const renderCell = (column, item) => {
    switch (column.dataType) {
      case "select":
        return (
          <Checkbox
            checked={tableData.selectedIds?.has(item.id) || false}
            onChange={() => onToggle(item)}
          />
        );
      case "image":
        return (
          <Avatar
            src={item[column.id]}
            alt={`${column.label} for ${item.id}`}
            sx={{ width: 40, height: 40 }}
          />
        );
      case "date":
        return new Date(item[column.id]).toLocaleDateString();
      case "datetime":
        return new Date(item[column.id]).toLocaleString();
      case "number":
        return Number(item[column.id]).toLocaleString();
      default: // "string" and any unhandled types
        return item[column.id];
    }
  };

  const tableContent = useMemo(
    () => (
      <TableContainer
        component={Paper}
        style={{ maxHeight: 400, overflow: "auto" }}
      >
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {tableData.columns.map((column) => (
                <TableCell
                  key={column.id}
                  style={{ backgroundColor: "#f5f5f5" }}
                  sortDirection={orderBy === column.id ? order : false}
                >
                  <TableSortLabel
                    active={orderBy === column.id}
                    direction={orderBy === column.id ? order : "asc"}
                    onClick={() => handleSort(column.id)}
                  >
                    {column.label}
                  </TableSortLabel>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((item) => (
              <TableRow key={item.id}>
                {tableData.columns.map((column) => (
                  <TableCell key={`${item.id}-${column.id}`}>
                    {renderCell(column, item)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    ),
    [paginatedData, tableData.columns, tableData.selectedIds, orderBy, order]
  );

  return (
    <Box>
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        margin="normal"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
          endAdornment: searchTerm && (
            <InputAdornment position="end">
              <IconButton onClick={() => setSearchTerm("")} edge="end">
                <ClearIcon />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
      {tableContent}
      {paginate && (
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredData.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      )}
    </Box>
  );
};

export default CustomTable;
