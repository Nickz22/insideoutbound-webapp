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
          <TableRow style={{ backgroundColor: "#f5f5f5" }}>
            {" "}
            {columns.map((column) => (
              <TableCell key={column.id} style={{ backgroundColor: "#f5f5f5" }}>
                {" "}
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
                  {column.id === "select" ? (
                    <Checkbox
                      checked={column.selectedIds.has(item.Id)}
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
