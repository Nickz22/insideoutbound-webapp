import React, { useState, useMemo } from "react";
import {
  Table,
  Paper,
  TableContainer,
  TablePagination,
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Menu,
  MenuItem,
  Modal,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Avatar,
  Divider,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";
import TableHeader from "./TableHeader";
import TableBody from "./TableBody";
import { sortData, filterData } from "../../utils/data";

/**
 * @typedef {import('types').TableColumn} TableColumn
 * @typedef {import('types').TableData} TableData
 */

/**
 * @param {{
 *   tableData: TableData,
 *   onSelectionChange: (selectedIds: Set<string>) => void,
 *   onColumnsChange: (columns: TableColumn[]) => void,
 *   paginate?: boolean,
 *   onRowClick: (item: Record<string, any>) => void
 * }} props
 */
const CustomTable = ({
  tableData,
  onSelectionChange,
  onColumnsChange,
  paginate = false,
  onRowClick,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [orderBy, setOrderBy] = useState("");
  const [order, setOrder] = useState("asc");
  const [contextMenu, setContextMenu] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedRowId, setSelectedRowId] = useState(null);

  const filteredData = useMemo(() => {
    return filterData(tableData.data, searchTerm);
  }, [tableData.data, searchTerm]);

  const sortedData = useMemo(() => {
    return sortData(filteredData, orderBy, order);
  }, [filteredData, orderBy, order]);

  const paginatedData = useMemo(() => {
    if (!paginate) return sortedData;
    const startIndex = page * rowsPerPage;
    return sortedData.slice(startIndex, startIndex + rowsPerPage);
  }, [sortedData, page, rowsPerPage, paginate]);

  const handleContextMenu = (event) => {
    event.preventDefault();
    setContextMenu(
      contextMenu === null
        ? { mouseX: event.clientX - 2, mouseY: event.clientY - 4 }
        : null
    );
  };

  const handleCloseContextMenu = () => {
    setContextMenu(null);
  };

  const handleOpenModal = () => {
    setModalOpen(true);
    handleCloseContextMenu();
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const handleColumnToggle = (column) => {
    const newColumns = tableData.columns.includes(column)
      ? tableData.columns.filter((c) => c.id !== column.id)
      : [...tableData.columns, column];
    onColumnsChange(newColumns);
  };

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

  const handleToggle = (item) => {
    const newSelectedIds = new Set(tableData.selectedIds);
    if (newSelectedIds.has(item.id)) {
      newSelectedIds.delete(item.id);
    } else {
      newSelectedIds.add(item.id);
    }
    onSelectionChange(newSelectedIds);
  };

  const handleRowClick = (item) => {
    setSelectedRowId(item.id);
    if (onRowClick) {
      onRowClick(item);
    }
  };

  /**
   * @param {TableColumn} column
   * @param {Record<string, any>} item
   */
  const renderCell = (column, item) => {
    let element;
    switch (column.dataType) {
      case "select":
        element = (
          <Checkbox
            checked={tableData.selectedIds.has(item.id) || false}
            onChange={() => handleToggle(item)}
          />
        );
        break;
      case "image":
        element = (
          <Avatar
            src={item[column.id]}
            alt={`${column.label} for ${item.id}`}
            sx={{ width: 40, height: 40 }}
          />
        );
        break;
      case "date":
        if (item[column.id]) {
          element = new Date(item[column.id]).toLocaleDateString();
          break;
        }
        element = null;
        break;
      case "datetime":
        if (item[column.id]) {
          element = new Date(item[column.id]).toLocaleString();
          break;
        }
        element = null;
        break;
      case "number":
        element = Number(item[column.id]).toLocaleString();
        break;
      default:
        element = item[column.id];
        break;
    }

    return element;
  };

  const tableContent = useMemo(
    () => (
      <TableContainer
        component={Paper}
        style={{ maxHeight: 400, overflow: "auto" }}
      >
        <Table stickyHeader>
          <TableHeader
            columns={tableData.columns}
            orderBy={orderBy}
            order={order}
            onSort={handleSort}
            onContextMenu={handleContextMenu}
          />
          <TableBody
            data={paginatedData}
            columns={tableData.columns}
            renderCell={renderCell}
            onRowClick={handleRowClick}
            selectedRowId={selectedRowId}
          />
        </Table>
      </TableContainer>
    ),
    [paginatedData, tableData.columns, tableData.selectedIds, orderBy, order, selectedRowId]
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
      {paginate && tableData.data && (
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
      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        <MenuItem onClick={handleOpenModal}>Manage Columns</MenuItem>
      </Menu>
      <Modal
        open={modalOpen}
        onClose={handleCloseModal}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 400,
            maxHeight: "80vh", // Limit the height to 80% of the viewport height
            bgcolor: "background.paper",
            border: "1px solid #000",
            boxShadow: 24,
            p: 4,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Typography
            id="modal-modal-title"
            variant="h6"
            component="h2"
            gutterBottom
          >
            Manage Columns
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <List
            sx={{
              flexGrow: 1,
              overflow: "auto", // Make the list scrollable
              "& .MuiListItem-root": {
                paddingTop: 0.5,
                paddingBottom: 0.5,
              },
            }}
          >
            {tableData.availableColumns?.map((column) => (
              <ListItem
                key={column.id}
                dense
                button
                onClick={() => handleColumnToggle(column)}
              >
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={tableData.columns.some((c) => c.id === column.id)}
                    tabIndex={-1}
                    disableRipple
                  />
                </ListItemIcon>
                <ListItemText primary={column.label} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Modal>
    </Box>
  );
};

export default CustomTable;
