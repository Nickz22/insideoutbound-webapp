import React, { useEffect, useState } from 'react';
import { Box, Button, CircularProgress, FormControl, MenuItem, Select } from '@mui/material';
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

/** @return {TableData|null} */
const initTableData = () => {
    return null
}

/**
 * @param {object} props
 * @param {object} props.inputValues
 * @param {() => void} props.handleNext
 * @param {(event: import('@mui/material').SelectChangeEvent<string>, setting: string) => void} props.handleInputChange
 */
const RoleStep = (props) => {
    /** @type {[TableData|null, React.Dispatch<React.SetStateAction<(TableData|null)>>]} */
    const [tableData, setTableData] = useState(initTableData());
    const [isLoading, setIsLoading] = useState(false);
    const [role, setRole] = useState("")


    /** @param {Set<string>} newSelectedIds */
    const handleTableSelectionChange = (newSelectedIds) => {
        setTableData((prev) =>
            prev ? { ...prev, selectedIds: newSelectedIds } : null
        );
    };

    /** @param {TableColumn[]} newColumns */
    const handleColumnsChange = (newColumns) => {
        setTableData((prev) => (prev ? { ...prev, columns: newColumns } : null));
    };

    const fetchTableData = async () => {
        try {
            setIsLoading(true)
            const data = await fetchSalesforceUsers();

            /** @type {TableData} */
            const _tableData = {
                availableColumns: [],
                columns: COLUMNS,
                data: data.data,
                selectedIds: new Set(),
            };

            setTableData(_tableData);

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
            setTableData(null)
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
                justifyContent: "start",
                paddingTop: "85px",
                paddingBottom: "85px"
            }}
        >
            <div
                style={{
                    width: "100%",
                    maxWidth: "720px",
                    padding: "16px"
                }}
            >
                <p
                    style={{
                        margin: 0,
                        color: "rgba(30, 36, 47, 1)",
                        fontSize: "14px",
                        fontWeight: "500",
                        letterSpacing: "4.76px",
                        textAlign: "center"
                    }}
                >
                    YOUR DATA VISUALIZED
                </p>
                <h1
                    style={{
                        margin: 0,
                        color: "rgba(30, 36, 47, 1)",
                        fontSize: "88px",
                        fontWeight: "700",
                        letterSpacing: "-2.64px",
                        lineHeight: "1.2",
                        textAlign: "center"
                    }}
                >
                    Welcome to your
                </h1>
                <h1
                    style={{
                        margin: 0,
                        color: "rgba(30, 36, 47, 1)",
                        fontSize: "88px",
                        fontWeight: "700",
                        letterSpacing: "-2.64px",
                        lineHeight: "1.2",
                        textAlign: "center"
                    }}
                >
                    Onboarding
                </h1>
                <p
                    style={{
                        margin: 0,
                        marginTop: "2rem",
                        color: "rgba(76, 76, 76, 1)",
                        fontSize: "16px",
                        fontWeight: "400",
                        letterSpacing: "-0.48px",
                        lineHeight: "1.5",
                        textAlign: "center"
                    }}
                >
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida.
                </p>
                <Box
                    style={{
                        marginTop: "42px",
                        width: "588px",
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "center",
                        padding: "40px 72px",
                        boxShadow: "2px 13px 20.5px 1px rgba(0, 0, 0, 0.1)",
                        borderRadius: "49px"
                    }}
                >
                    <h2
                        style={{
                            fontWeight: "500",
                            fontSize: "32px",
                            letterSpacing: "-0.96px",
                            textAlign: "center",
                            color: "rgba(30, 36, 47, 1)",
                            lineHeight: "1",
                        }}
                    >
                        Tell Us About Yourself
                    </h2>
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
                        >
                            <MenuItem value={"placeholder"} sx={{ display: "none" }}>
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
                        {tableData && (
                            <CustomTable
                                tableData={tableData}
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

                            }}

                        >
                            Next
                        </Button>
                    </Box>
                </Box>
            </div >

        </Box >
    );
};

export default RoleStep;