import React, { useState } from 'react';
import { Box, Button, FormControl, MenuItem, Select } from '@mui/material';

/**
 * @typedef {import('types').Settings} Settings
 */

/**
 * @param {object} props
 * @param {() => void} props.handleNext
 */
const RoleStep = ({ handleNext }) => {
    /** @type {[Settings, React.Dispatch<React.SetStateAction<Settings>>]} */
    const [inputValues, setInputValues] = useState({
        userRole: "placeholder"
    });

    const handleInputChange = (event, setting) => {
        setInputValues((prev) => ({
            ...prev,
            [setting]: event.target.value,
        }));
    };

    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                flex: 1,
                backgroundColor: "white",
                maxWidth: "100%",
                overflow: "scroll",
                marginLeft: "425px",
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
                        {/* <InputLabel>User Role</InputLabel> */}
                        <Select
                            value={inputValues.userRole}
                            placeholder="User Role"
                            onChange={(e) => handleInputChange(e, "userRole")}
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
                            onClick={() => { handleNext() }}
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