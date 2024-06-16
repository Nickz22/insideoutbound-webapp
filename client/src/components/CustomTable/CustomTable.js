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
} from "@mui/material";

const CustomTable = ({ columns, data, onToggle }) => {
  return (
    <TableContainer
      component={Paper}
      style={{ maxHeight: 400, overflow: "auto" }}
    >
      <Table stickyHeader>
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell key={column.id}>{column.label}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((item) => (
            <TableRow key={item.id}>
              {columns.map((column) => (
                <TableCell key={`${item.id}-${column.id}`}>
                  {column.id === "select" ? (
                    <Checkbox
                      checked={column.selectedIds.has(item.id)}
                      onChange={() => onToggle(item)}
                    />
                  ) : (
                    item[column.id]
                  )}
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
