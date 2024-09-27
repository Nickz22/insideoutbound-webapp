import React from 'react'
import { Box, Divider, Grid, Typography } from '@mui/material'
import SummaryLineChartCard from 'src/components/SummaryCard/SummaryLineChartCard'
import SummaryBarChartCard from 'src/components/SummaryCard/SummaryBarChartCard'

/**
 * @typedef {object} SummaryData
 * @property {number} activations_today
 * @property {number} avg_contacts_per_account
 * @property {number} avg_tasks_per_contact
 * @property {number} closed_won_opportunity_value
 * @property {number} engaged_activations
 * @property {number} total_accounts
 * @property {number} total_activations
 * @property {number} total_active_contacts
 * @property {number} total_contacts
 * @property {number} total_deals
 * @property {number} total_events
 * @property {number} total_pipeline_value
 * @property {number} total_tasks
 * @property {{label: string, value: number}[]} activation_trend
 * @property {{label: string, value: number}[]} activities_type
 */

const activities_type = [
    {
        "label": "Call Connect",
        "value": 75
    },
    {
        "label": "Dial",
        "value": 112
    },
    {
        "label": "Inbound Email",
        "value": 90
    },
    {
        "label": "Outbound Email",
        "value": 400
    }
];

const activation_trend = [
    {
        "label": "2024/09/12",
        "value": 75
    },
    {
        "label": "2024/09/13",
        "value": 112
    },
    {
        "label": "2024/09/14",
        "value": 90
    },
    {
        "label": "2024/09/15",
        "value": 400
    }
];

/**
 * @param {object} props
 * @param {SummaryData} props.summaryData
 * @param {string} props.period
 */
const ProspectingSummary = ({ summaryData, period }) => {
    return (
        <>
            {/* First Row */}
            <Grid container columnGap={"32px"} display={"grid"} gridTemplateColumns={"1fr 2fr"} >
                <Grid display={"flex"} flexDirection={"column"} gap={"20px"} padding={"16px"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="body1" textAlign={"center"}>{period} you started prospecting</Typography>
                    <Typography variant="h4" textAlign={"center"}>{summaryData.total_accounts} Accounts</Typography>
                </Grid>
                <Grid item padding={"16px"} sx={{ border: "1px solid #000000" }}>
                    <SummaryLineChartCard title='Activation Trend' data={activation_trend} />
                </Grid>
            </Grid>

            {/* Second Row */}
            <Box display={"grid"} marginTop={"20px"} columnGap={"32px"} gridTemplateColumns={"1fr 1fr"} >
                <Box padding={"16px"} gap={"20px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="h3">Prospecting Funnel</Typography>
                    <Box display={"flex"} width={"100%"} flexDirection={"column"} alignItems={"center"}>
                        <Box padding={"16px"} width={"80%"} borderRadius={"50px"} alignItems={"center"} justifyContent={"center"} display={"flex"} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">{summaryData.total_activations} Activated</Typography>
                        </Box>
                        <Divider sx={{ width: "2px", height: "40px", backgroundColor: "rgba(135, 159, 202, 0.5)" }} />
                        <Box padding={"16px"} width={"70%"} borderRadius={"50px"} alignItems={"center"} justifyContent={"center"} display={"flex"} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">{summaryData.engaged_activations} Engaged</Typography>
                        </Box>
                        <Divider sx={{ width: "2px", height: "40px", backgroundColor: "rgba(135, 159, 202, 0.5)" }} />
                        <Box padding={"16px"} width={"60%"} borderRadius={"50px"} alignItems={"center"} justifyContent={"center"} display={"flex"} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">[#] Meeting Set</Typography>
                        </Box>
                        <Divider sx={{ width: "2px", height: "40px", backgroundColor: "rgba(135, 159, 202, 0.5)" }} />
                        <Box padding={"16px"} width={"50%"} borderRadius={"50px"} alignItems={"center"} justifyContent={"center"} display={"flex"} flexDirection={"column"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">[#] Opportunity</Typography>
                        </Box>
                    </Box>
                </Box>

                <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="h3">Prospecting Width and Depth</Typography>
                    <Box display={"flex"} flexDirection={"row"} gap={"12px"}>
                        <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Average number of contacts approached per account</Typography>
                            <Typography variant="h2">{summaryData.avg_contacts_per_account}</Typography>
                        </Box>
                        <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Average number of activities logged per contact</Typography>
                            <Typography variant="h2">{summaryData.avg_tasks_per_contact}</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px 0px"} display={"flex"} flex={1} flexDirection={"column"} sx={{ border: "1px solid #000000", width: "100%" }}>
                        <SummaryBarChartCard direction='horizontal' title='Activities by Type' data={activities_type} />
                    </Box>
                </Box>
            </Box>


            {/* Third Row */}
            <Box display={"flex"} flexDirection={"row"} marginTop={"20px"} gap={"32px"} >
                <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="h3" textAlign={"center"}>Prospecting Outcomes</Typography>
                    <Box display={"flex"} flex={1} flexDirection={"row"} gap={"20px"}>
                        <Box gap={"20px"} padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Meeting Set</Typography>
                            <Typography variant="h2">16</Typography>
                        </Box>
                        <Box gap={"20px"} padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Opportunities Created</Typography>
                            <Typography variant="h2">5</Typography>
                        </Box>
                    </Box>

                    <Box display={"flex"} flex={1} flexDirection={"row"} gap={"20px"}>
                        <Box gap={"20px"} padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Opportunity Value</Typography>
                            <Typography variant="h2">{summaryData.closed_won_opportunity_value?.toLocaleString(undefined, { style: "currency", currency: "USD" })}</Typography>
                        </Box>
                        <Box gap={"20px"} padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Closed Won</Typography>
                            <Typography variant="h2">{summaryData.closed_won_opportunity_value?.toLocaleString(undefined, { style: "currency", currency: "USD" })}</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flexDirection={"column"} flex={1}>
                            <Typography variant="body1">Cycle Time</Typography>
                            <Typography variant="body1">(Average days from first activity to opportunity)</Typography>
                        </Box>
                        <Box width={"120px"}>
                            <Typography variant="h4" textAlign={"center"}>4.7</Typography>
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
                            <Typography variant="h4" textAlign={"center"}>{isFinite(summaryData.total_activations / summaryData.engaged_activations) ? summaryData.total_activations / summaryData.engaged_activations : 0}</Typography>
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