import React from 'react'
import { Box, Divider, Typography } from '@mui/material'

const ProspectingSummary = () => {
    return (
        <>
            {/* First Row */}
            <Box display={"flex"} flexDirection={"row"} gap={"32px"} >
                <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="body1" textAlign={"center"}>This month you started prospecting</Typography>
                    <Typography variant="h4" textAlign={"center"}>60 Accounts</Typography>
                </Box>
                <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="h4" textAlign={"center"}>Activation Trend</Typography>
                    <Typography variant="h4" textAlign={"center"}>Line graph here</Typography>
                </Box>
            </Box>

            {/* Second Row */}
            <Box display={"flex"} flexDirection={"row"} marginTop={"20px"} gap={"32px"} >
                <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="h3">Prospecting Funnel</Typography>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                        <Typography variant="body1">[#] Activated</Typography>
                    </Box>
                    <Divider sx={{ width: "2px", height: "20px", backgroundColor: "rgba(135, 159, 202, 0.5)" }} />
                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                        <Typography variant="body1">[#] Engaged</Typography>
                    </Box>
                    <Divider sx={{ width: "2px", height: "20px", backgroundColor: "rgba(135, 159, 202, 0.5)" }} />
                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                        <Typography variant="body1">[#] Meeting Set</Typography>
                    </Box>
                    <Divider sx={{ width: "2px", height: "20px", backgroundColor: "rgba(135, 159, 202, 0.5)" }} />
                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                        <Typography variant="body1">[#] Opportunity</Typography>
                    </Box>
                </Box>

                <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="h3">Prospecting Width and Depth</Typography>
                    <Box display={"flex"} flexDirection={"row"} gap={"12px"}>
                        <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Average number of contacts approached per account</Typography>
                            <Typography variant="h2">4.7</Typography>
                        </Box>
                        <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Average number of activities logged per contact</Typography>
                            <Typography variant="h2">8.2</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                        <Typography variant="h4" textAlign={"center"}>Activities by Type</Typography>
                        <Typography variant="h4" textAlign={"center"}>Bar graph here</Typography>
                    </Box>
                </Box>
            </Box>


            {/* Third Row */}
            <Box display={"flex"} flexDirection={"row"} marginTop={"20px"} gap={"32px"} >
                <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="h3" textAlign={"center"}>Prospecting Outcomes</Typography>
                    <Box display={"flex"} flex={1} flexDirection={"row"} gap={"20px"}>
                        <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Meeting Set</Typography>
                            <Typography variant="h4">16</Typography>
                        </Box>
                        <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Opportunities Created</Typography>
                            <Typography variant="h4">5</Typography>
                        </Box>
                    </Box>

                    <Box display={"flex"} flex={1} flexDirection={"row"} gap={"20px"}>
                        <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Opportunity Value</Typography>
                            <Typography variant="h4">$326,000</Typography>
                        </Box>
                        <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Closed Won</Typography>
                            <Typography variant="h4">$106,000</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flexDirection={"column"} flex={1}>
                            <Typography variant="body1">Cycle Time</Typography>
                            <Typography variant="body1">(Average days from first activity to opportunity)</Typography>
                        </Box>
                        <Box display={"flex"} alignItems={"center"}>
                            <Typography variant="h4">4.7</Typography>
                        </Box>
                    </Box>
                </Box>

                <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000" }} gap={"20px"}>
                    <Typography variant="h3">What Moves the Needle?</Typography>
                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flex={1}>
                            <Typography>How many activities does it take, on average, to get account to engage with you?</Typography>
                        </Box>
                        <Box width={"160px"}>
                            <Typography variant="h4" textAlign={"center"}>13.7</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flex={1}>
                            <Typography>How many contacts do you approach on average, before getting a response from someone in the account?</Typography>
                        </Box>
                        <Box width={"160px"}>
                            <Typography variant="h4" textAlign={"center"}>3.1</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flex={1}>
                            <Typography>What type of activity most strongly correlates with prospect responses?</Typography>
                        </Box>
                        <Box width={"160px"}>
                            <Typography variant="h4" textAlign={"center"}>Outbound email</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flex={1}>
                            <Typography>What type of activity most strongly correlates with setting a meeting?</Typography>
                        </Box>
                        <Box width={"160px"}>
                            <Typography variant="h4" textAlign={"center"}>Call Connect</Typography>
                        </Box>
                    </Box>
                </Box>
            </Box>
        </>
    )
}

export default ProspectingSummary