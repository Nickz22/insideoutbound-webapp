import React from "react";
import { TableBody as MuiTableBody, TableRow, TableCell } from "@mui/material";

const TableBody = ({ data, columns, renderCell, onRowClick, selectedRowId }) => {
  return (
    <MuiTableBody>
      {data.map((item) => (
        <TableRow
          key={item.id}
          onClick={() => onRowClick && onRowClick(item)}
          style={{ cursor: onRowClick ? "pointer" : "default" }}
          sx={{
            "&:hover": {
              backgroundColor: "#f0e6dc", // Slightly more neutral than peachpuff for hover
            },
            backgroundColor: selectedRowId === item.id ? "#f0e6dc" : "inherit", // Darker gray for selected row
          }}
        >
          {columns.map((column) => (
            <TableCell key={`${item.id}-${column.id}`}>
              {renderCell(column, item)}
            </TableCell>
          ))}
        </TableRow>
      ))}
    </MuiTableBody>
  );
};

export default TableBody;
