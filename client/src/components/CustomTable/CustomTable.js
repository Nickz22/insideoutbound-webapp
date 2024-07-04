import React from "react";
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
} from "@mui/material";

/**
 * @typedef {Object} TableColumn
 * @property {string} id
 * @property {"string" | "number" | "date" | "datetime" | "select" | "image"} dataType
 * @property {string} label
 * @property {Set<string>} [selectedIds]
 */

/**
 * @typedef {Object} TableData
 * @property {string} Id
 * @property {any} [key: string]
 */

/**
 * @param {Object} props
 * @param {TableColumn[]} props.columns
 * @param {TableData[]} props.data
 * @param {(item: TableData) => void} props.onToggle
 */
const CustomTable = ({ columns, data, onToggle }) => {
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
            checked={column.selectedIds?.has(item.Id) || false}
            onChange={() => onToggle(item)}
          />
        );
      case "image":
        return (
          <Avatar
            src={item[column.id]}
            alt={`${column.label} for ${item.Id}`}
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

  return (
    <TableContainer
      component={Paper}
      style={{ maxHeight: 400, overflow: "auto" }}
    >
      <Table stickyHeader>
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell key={column.id} style={{ backgroundColor: "#f5f5f5" }}>
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((item) => (
            <TableRow key={item.Id}>
              {columns.map((column) => (
                <TableCell key={`${item.Id}-${column.id}`}>
                  {renderCell(column, item)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default CustomTable;
