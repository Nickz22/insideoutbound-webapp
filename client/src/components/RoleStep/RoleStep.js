import React, { useEffect, useState } from 'react';
import { Box, Button, CircularProgress, FormControl, MenuItem, Select, Typography } from '@mui/material';
import CustomTable from 'src/components/CustomTable/CustomTable';
import { fetchSalesforceUsers } from 'src/components/Api/Api';

/**
 * @typedef {import('types').Settings} Settings
 * @typedef {import('types').TableColumn} TableColumn
 * @typedef {import('types').TableData} TableData
 */

/** @type {TableColumn[]} */
const COLUMNS = [
    {
        id: "select",
        label: "Select",
        dataType: "select",
    },
    {
        id: "photoUrl",
        label: "",
        dataType: "image",
    },
    {
        id: "firstName",
        label: "First Name",
        dataType: "string",
    },
    {
        id: "lastName",
        label: "Last Name",
        dataType: "string",
    },
    {
        id: "email",
        label: "Email",
        dataType: "string",
    },
    {
        id: "role",
        label: "Role",
        dataType: "string",
    },
    {
        id: "username",
        label: "Username",
        dataType: "string",
    },
]


/**
 * @param {object} props
 * @param {object} props.inputValues
 * @param {() => void} props.handleNext
 * @param {(event: import('@mui/material').SelectChangeEvent<string>, setting: string) => void} props.handleInputChange
 * @param {TableData | null} props.tableData
 * @param {React.Dispatch<React.SetStateAction<(TableData|null)>>} props.setTableData
 */
const RoleStep = (props) => {
    const [isLoading, setIsLoading] = useState(false);
    const [role, setRole] = useState(props.inputValues.userRole)


    /** @param {Set<string>} newSelectedIds */
    const handleTableSelectionChange = (newSelectedIds) => {
        props.setTableData((prev) =>
            prev ? { ...prev, selectedIds: newSelectedIds } : null
        );
    };

    /** @param {TableColumn[]} newColumns */
    const handleColumnsChange = (newColumns) => {
        props.setTableData((prev) => (prev ? { ...prev, columns: newColumns } : null));
    };

    const fetchTableData = async () => {
        if (props.tableData) {
            return;
        }

        try {
            setIsLoading(true)
            const data = await fetchSalesforceUsers();

            /** @type {TableData} */
            const _tableData = {
                availableColumns: COLUMNS,
                columns: COLUMNS,
                data: data.data,
                selectedIds: props.tableData?.selectedIds ? props.tableData.selectedIds : new Set(), // prevent data resetting
            };

            props.setTableData(_tableData);

        } catch (error) {
            console.error("Error fetching data:", error);
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        if (role === "I manage a team") {
            fetchTableData()
        } else {
            props.setTableData(null)
        }
    }, [role])

    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                flex: 1,
                backgroundColor: "white",
                maxWidth: "100%",
                position: "relative",
                alignItems: "center",
                justifyContent: "center",
                paddingTop: "85px",
                paddingBottom: "85px"
            }}
        >
            <Box
                sx={{
                    width: "100%",
                    padding: "16px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    boxShadow: "none"
                }}
            >
                <Box sx={{
                    width: "100%",
                    maxWidth: "710px",
                    flexDirection: "column",
                    alignItems: "center",
                    display: "flex"
                }}>
                    <Typography
                        variant='subtitle1'
                        style={{
                            color: "rgba(30, 36, 47, 1)",
                            letterSpacing: "4.76px",
                            textAlign: "center"
                        }}
                    >
                        YOUR DATA VISUALIZED
                    </Typography>
                    <Typography
                        variant='display1'
                        style={{
                            color: "rgba(30, 36, 47, 1)",
                            letterSpacing: "-2.64px",
                            lineHeight: "0.98",
                            textAlign: "center"
                        }}
                    >
                        Welcome to your
                    </Typography>
                    <Typography
                        variant='display1'
                        style={{
                            color: "rgba(30, 36, 47, 1)",
                            letterSpacing: "-2.64px",
                            lineHeight: "0.98",
                            textAlign: "center"
                        }}
                    >
                        Onboarding
                    </Typography>
                    <Typography
                        variant='body1'
                        style={{
                            margin: 0,
                            marginTop: "2rem",
                            color: "rgba(76, 76, 76, 1)",
                            textAlign: "center"
                        }}
                    >
                        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida.
                    </Typography>
                </Box>
                <Box
                    style={{
                        marginTop: "42px",
                        minWidth: "600px",
                        maxWidth: "100%",
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "center",
                        padding: "40px 72px",
                        boxShadow: "2px 13px 20.5px 1px rgba(0, 0, 0, 0.1)",
                        borderRadius: "49px"
                    }}
                >
                    <Typography
                        variant='h3'
                        style={{
                            letterSpacing: "-0.96px",
                            textAlign: "center",
                            color: "rgba(30, 36, 47, 1)",
                        }}
                    >
                        Tell Us About Yourself
                    </Typography>
                    <FormControl fullWidth variant="outlined" margin="normal">
                        <Select
                            value={props.inputValues.userRole}
                            placeholder="User Role"
                            onChange={(e) => {
                                setRole(e.target.value);
                                props.handleInputChange(e, "userRole");
                            }}
                            label={"User Role"}
                            variant='standard'
                            fullWidth
                            sx={{
                                color: "rgba(83, 58, 243, 1)",
                                fontWeight: "400",
                                fontSize: "26px",
                                letterSpacing: "-0.78px",
                                borderBottom: "1px solid rgba(83, 58, 243, 1)",
                                "::before": {
                                    borderBottom: "none"
                                },
                                "::after": {
                                    borderBottom: "none"
                                },
                                ":hover": {
                                    borderBottom: "2px solid rgba(83, 58, 243, 1)",
                                },
                                ":hover:not(.Mui-disabled, .Mui-error):before": {
                                    borderBottom: "2px solid rgba(83, 58, 243, 1)",
                                },
                                ":hover::after": {
                                    borderBottom: "none",
                                }
                            }}
                            displayEmpty
                        >
                            <MenuItem value={""} sx={{ display: "none" }}>
                                User Role
                            </MenuItem>
                            {["I manage a team", "I am an individual contributor"].map((option, index) => (
                                <MenuItem
                                    key={index}
                                    value={option}
                                >
                                    {option}
                                </MenuItem>
                            ))}
                        </Select>
                        {props.tableData && (
                            <CustomTable
                                tableData={props.tableData}
                                onRowClick={() => { return; }}
                                onSelectionChange={handleTableSelectionChange}
                                onColumnsChange={handleColumnsChange}
                                paginate={true}
                            />)}
                        {isLoading && (
                            <Box
                                sx={{
                                    display: "flex",
                                    flexDirection: "column",
                                    alignItems: "center",
                                    marginTop: "29px",
                                }}
                            >
                                <CircularProgress size={30} />
                            </Box>
                        )}
                    </FormControl>
                    <Box
                        sx={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            marginTop: "29px",
                        }}
                    >
                        <Button
                            onClick={props.handleNext}
                            variant="contained"
                            color="primary"
                            sx={{
                                background: "linear-gradient(131.16deg, #FF7D2F 24.98%, #491EFF 97.93%)",
                                width: "271px",
                                height: "52px",
                                borderRadius: "40px",
                                fontWeight: "700",
                                fontSize: "32px",
                                letterSpacing: "-0.96px",
                                textTransform: "none"
                            }}

                        >
                            Next
                        </Button>
                    </Box>
                </Box>
            </Box >

        </Box >
    );
};

export default RoleStep;