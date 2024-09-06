import React from 'react'
import { useOnboard } from './OnboardProvider';
import { Box, Button, styled, TextField } from '@mui/material';

const StyledTextField = styled(TextField)({
    '& .MuiInputLabel-root': {
        color: '#533AF3', // Adjust the color to match the blue color in the image
        fontSize: '22px', // Larger font size
        fontWeight: 'normal', // Normal font weight
    },
    '& .MuiInputLabel-root.Mui-focused': {
        color: '#533AF3', // Adjust the color to match the blue color in the image
        fontSize: '22px', // Larger font size
        fontWeight: 'normal', // Normal font weight
        fontFamiliy: '"Albert Sans", sans-serif'
    },
    '& .MuiInput-underline:before': {
        borderBottomColor: '#533AF3', // Blue underline
    },
    '& .MuiInput-underline:hover:not(.Mui-disabled):before': {
        borderBottomColor: '#533AF3', // Blue underline on hover
    },
    '& .MuiInput-underline:after': {
        borderBottomColor: '#533AF3', // Blue underline after focus
    },
    '& .MuiInputBase-input': {
        fontSize: '16px',
        marginTop: "16px"
    },
});

const ActivityPerContactStep = () => {
    const { inputValues, setInputValues, step, setStep } = useOnboard();

    /**
     * @param {import('react').ChangeEvent<HTMLInputElement | HTMLTextAreaElement>} event
     * @param {string} setting
     */
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
                <h1
                    style={{
                        margin: 0,
                        color: "rgba(30, 36, 47, 1)",
                        fontSize: "88px",
                        fontWeight: "700",
                        letterSpacing: "-2.64px",
                        lineHeight: "1.2",
                        textAlign: "left"
                    }}
                >
                    Activities per Contact
                </h1>
                <p>Great — we have a definition for prospecting at the company level! Next, we need to do the same thing for the people who work at target companies.</p>
                <p style={{ marginTop: "2rem" }}>Help us fill in the blank below:</p>
                <p style={{ marginTop: "2rem" }}>Please start by filling out the blanks below:</p>
                <p style={{ marginTop: "2rem" }}>Once a rep logs {inputValues.activitiesPerContact} attempts to contact an individual (emails, calls, InMails, etc.), we consider that prospecting</p>


                <StyledTextField
                    value={inputValues["activitiesPerContact"]}
                    onChange={(e) => handleInputChange(e, "activitiesPerContact")}
                    label={"# activities per contact"}
                    type="number"
                    variant="standard"
                    InputLabelProps={{
                        shrink: true,
                    }}
                    sx={{
                        marginTop: "48px"
                    }}
                    fullWidth
                />

                <Box
                    sx={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        marginTop: "29px",
                    }}
                >
                    <Button
                        onClick={() => { setStep(step + 1); }}
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
            </div>
        </Box>
    )
};

export default ActivityPerContactStep;