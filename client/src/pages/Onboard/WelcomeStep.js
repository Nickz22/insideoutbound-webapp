import React from 'react'
import { Box, Button, styled, TextField } from '@mui/material'
import { useOnboard } from './OnboardProvider'

// Custom styled component to match the design
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

const WelcomeStep = () => {
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
                    Welcome
                </h1>
                <p>Our goal is to help you better measure and manage your account-based prospecting efforts.</p>
                <p style={{ marginTop: "2rem" }}>To do that, <b>we need to define prospecting</b>. {`The term we use is an "approach". Clearly defining an approach helps us differentiate prospecting efforts from all other stuff sales reps do, like working deals or sending one-off emails.`}</p>
                <p style={{ marginTop: "2rem" }}>Please start by filling out the blanks below:</p>
                <p style={{ marginTop: "2rem" }}>{`An "approach" is defined as when a rep attempts to engage with ${inputValues.contactsPerAccount || "_"} people at a target/prospect company within a ${inputValues.trackingPeriod || "_"} day period.`}</p>

                <StyledTextField
                    value={inputValues["contactsPerAccount"]}
                    onChange={(e) => handleInputChange(e, "contactsPerAccount")}
                    label="Number of Engaged People"
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

                <StyledTextField
                    value={inputValues["trackingPeriod"]}
                    onChange={(e) => handleInputChange(e, "trackingPeriod")}
                    label={"Tracking Period"}
                    type="number"
                    variant="standard"
                    InputLabelProps={{
                        shrink: true,
                    }}
                    sx={{
                        marginTop: "48px"
                    }}
                    margin='normal'
                    fullWidth
                />
                <Box
                    sx={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        marginTop: "56px",
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
}

export default WelcomeStep