import React, { useState, useMemo, useEffect } from "react";
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
    CircularProgress,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";
import TableHeader from "./TableHeader";
import TableBody from "./TableBody";
import { sortData } from "../../utils/data";
import { debounce } from "lodash"; // Add this import at the top of the file

/**
 * @typedef {import('types').TableColumn} TableColumn
 * @typedef {import('types').TableData} TableData
 */

/**
 * @typedef {Object} PaginationConfig
 * @property {"client-side" | "server-side"} type
 * @property {number} [totalItems]
 * @property {number} [page]
 * @property {number} [rowsPerPage]
 * @property {(page: number, rowsPerPage: number) => void} [onPageChange]
 * @property {(rowsPerPage: number) => void} [onRowsPerPageChange]
 */

/**
 * @typedef {Object} SortConfig
 * @property {string} [columnId]
 * @property {"asc" | "desc"} [order]
 * @property {(columnId: string, order: "asc" | "desc") => void} [onSort]
 */

/**
 * @param {{
 *   tableData: TableData,
 *   onSelectionChange: (selectedIds: Set<string>) => void,
 *   onColumnsChange: (columns: TableColumn[]) => void,
 *   paginationConfig?: PaginationConfig | undefined,
 *   sortConfig?: SortConfig | undefined,
 *   onRowClick: (item: Record<string, any>) => void,
 *   isLoading: boolean
 *   onSearch: (value: string) => void | undefined
 * }} props
 */
const CustomTable = ({
    tableData,
    onSelectionChange,
    onColumnsChange,
    paginationConfig,
    sortConfig,
    onRowClick,
    isLoading,
    onSearch,
}) => {
    const [searchTerm, setSearchTerm] = useState("");
    const [localFilteredData, setLocalFilteredData] = useState(tableData.data);
    const [page, setPage] = useState(paginationConfig?.page);
    const [rowsPerPage, setRowsPerPage] = useState(
        paginationConfig?.rowsPerPage || 10
    );
    const [orderBy, setOrderBy] = useState(sortConfig?.columnId || "");
    const [order, setOrder] = useState(sortConfig?.order || "asc");
    const [contextMenu, setContextMenu] = useState(null);
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedRowId, setSelectedRowId] = useState(null);

    const isPaginated = !!paginationConfig;
    const isServerSidePaginated =
        isPaginated && paginationConfig.type === "server-side";

    const filteredData = useMemo(() => {
        return isServerSidePaginated ? tableData.data : localFilteredData;
    }, [tableData.data, localFilteredData, isServerSidePaginated]);

    const sortedData = useMemo(() => {
        return isServerSidePaginated
            ? filteredData
            : sortData(filteredData, orderBy, order);
    }, [filteredData, orderBy, order, isServerSidePaginated]);

    const paginatedData = useMemo(() => {
        if (!isPaginated) return sortedData;
        if (isServerSidePaginated) return sortedData;
        const startIndex = page * rowsPerPage;
        return sortedData.slice(startIndex, startIndex + rowsPerPage);
    }, [sortedData, page, rowsPerPage, isPaginated, isServerSidePaginated]);

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
        if (isServerSidePaginated && paginationConfig.onPageChange) {
            paginationConfig.onPageChange(newPage, rowsPerPage);
        }
    };

    const handleChangeRowsPerPage = (event) => {
        const newRowsPerPage = parseInt(event.target.value, 10);
        setRowsPerPage(newRowsPerPage);
        setPage(0);
        if (isServerSidePaginated && paginationConfig.onRowsPerPageChange) {
            paginationConfig.onRowsPerPageChange(newRowsPerPage);
        }
    };

    const handleSort = (columnId) => {
        const isAsc = orderBy === columnId && order === "asc";
        const newOrder = isAsc ? "desc" : "asc";
        setOrder(newOrder);
        setOrderBy(columnId);

        if (sortConfig?.onSort) {
            sortConfig.onSort(columnId, newOrder);
        }
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
                    {isLoading ? (
                        <tbody>
                            <tr>
                                <td
                                    colSpan={tableData.columns.length}
                                    style={{
                                        textAlign: "center",
                                        padding: "20px",
                                    }}
                                >
                                    <CircularProgress />
                                </td>
                            </tr>
                        </tbody>
                    ) : (
                        <TableBody
                            data={paginatedData}
                            columns={tableData.columns}
                            renderCell={renderCell}
                            onRowClick={handleRowClick}
                            selectedRowId={selectedRowId}
                        />
                    )}
                </Table>
            </TableContainer>
        ),
        [
            paginatedData,
            tableData.columns,
            tableData.selectedIds,
            orderBy,
            order,
            selectedRowId,
            isLoading,
        ]
    );

    // Create a debounced version of the search function
    const debouncedSearch = useMemo(
        () =>
            debounce((value) => {
                if (paginationConfig?.type === "server-side") {
                    if (value.length > 3 || value.length === 0) {
                        onSearch(value);
                    }
                } else {
                    // Perform local wildcard search on all columns
                    const filtered = tableData.data.filter((item) =>
                        Object.values(item).some((field) =>
                            String(field)
                                .toLowerCase()
                                .includes(value.toLowerCase())
                        )
                    );
                    setLocalFilteredData(filtered);
                    setPage(0); // Reset to first page when filtering
                }
            }, 2000),
        [paginationConfig, onSearch, tableData.data]
    );

    // Update the handleSearch function
    const handleSearch = (value) => {
        setSearchTerm(value);
        debouncedSearch(value);
    };

    // force a re-render when the sort order changes
    useEffect(() => {
        setPage(0);
    }, [orderBy, order]);

    return (
        <Box>
            <TextField
                fullWidth
                variant="outlined"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                margin="normal"
                InputProps={{
                    startAdornment: (
                        <InputAdornment position="start">
                            <SearchIcon />
                        </InputAdornment>
                    ),
                    endAdornment: searchTerm && (
                        <InputAdornment position="end">
                            <IconButton
                                onClick={() => handleSearch("")}
                                edge="end"
                            >
                                <ClearIcon />
                            </IconButton>
                        </InputAdornment>
                    ),
                }}
            />
            {tableContent}
            {isPaginated && (
                <TablePagination
                    rowsPerPageOptions={[5, 10, 25, 50]}
                    component="div"
                    count={
                        isServerSidePaginated
                            ? paginationConfig.totalItems || 0
                            : filteredData.length
                    }
                    rowsPerPage={rowsPerPage}
                    page={page || 0}
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
                                        checked={tableData.columns.some(
                                            (c) => c.id === column.id
                                        )}
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
