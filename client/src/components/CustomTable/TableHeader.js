import React from "react";
import {
  TableHead,
  TableRow,
  TableCell,
  TableSortLabel,
  Tooltip,
} from "@mui/material";

const TableHeader = ({ columns, orderBy, order, onSort, onContextMenu }) => {
  return (
    <TableHead>
      <TableRow onContextMenu={onContextMenu}>
        {columns.map((column) => (
          <Tooltip key={column.id} title="Right-click for more columns" arrow>
            <TableCell
              style={{ backgroundColor: "#f5f5f5" }}
              sortDirection={orderBy === column.id ? order : false}
            >
              <TableSortLabel
                active={orderBy === column.id}
                direction={orderBy === column.id ? order : "asc"}
                onClick={() => onSort(column.id)}
              >
                {column.label}
              </TableSortLabel>
            </TableCell>
          </Tooltip>
        ))}
      </TableRow>
    </TableHead>
  );
};

export default TableHeader;
