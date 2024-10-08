import React, { useMemo } from 'react'
import { Box, Grid, Typography, Tooltip } from '@mui/material'
import SummaryLineChartCard from 'src/components/SummaryCard/SummaryLineChartCard'
import SummaryBarChartCard from 'src/components/SummaryCard/SummaryBarChartCard'
import CustomFunnelChart from 'src/components/FunnelChart/FunnelChart'

/**
 * @typedef {object} SummaryData
 * @property {number} activations_today
 * @property {number} avg_contacts_per_account
 * @property {number} avg_outbound_activities_to_inbound_response
 * @property {number} avg_tasks_per_contact
 * @property {number} closed_won_opportunity_value
 * @property {number} avg_days_from_first_activity_to_opportunity
 * @property {number} engaged_activations
 * @property {number} in_status_activated
 * @property {number} in_status_engaged
 * @property {number} in_status_meeting_set
 * @property {number} in_status_opportunity_created
 * @property {number} avg_number_approached_contacts_to_engage
 * @property {number} most_effective_prospecting_activity_for_engagement
 * @property {number} most_effective_prospecting_activity_for_engagement_fraction
 * @property {number} most_effective_prospecting_activity_for_meeting
 * @property {number} most_effective_prospecting_activity_for_meeting_fraction
 * @property {number} total_accounts
 * @property {number} total_activations
 * @property {number} total_active_contacts
 * @property {number} total_contacts
 * @property {number} total_deals
 * @property {number} total_events
 * @property {number} total_pipeline_value
 * @property {number} total_tasks
 * @property {{label: string, value: number}[]} activation_trend
 * @property {{label: string, value: number}[]} prospecting_metadata_count_by_name
 */

/**
 * @param {object} props
 * @param {SummaryData} props.summaryData
 * @param {string} props.period
 */
const ProspectingSummary = ({ summaryData, period }) => {
    const activationTrendData = useMemo(() => {
        if (!summaryData || !summaryData.activation_trend) {
            return [];
        }
        return Object.entries(summaryData.activation_trend).map(([date, count]) => {
            // Parse the ISO date string
            const parsedDate = new Date(date);
            // Format the date as needed, e.g., "MM/DD"
            const formattedDate = `${parsedDate.getMonth() + 1}/${parsedDate.getDate()}`;
            return {
                label: formattedDate,
                value: count
            };
        }).sort((a, b) => new Date(a.label) - new Date(b.label)); // Sort by date
    }, [summaryData]);

    const prospectingActivityData = useMemo(() => {
        if (!summaryData || !summaryData.prospecting_metadata_count_by_name) {
            return [];
        }
        return Object.entries(summaryData.prospecting_metadata_count_by_name)
            .map(([name, value]) => ({
                label: name,
                value: value
            }))
            .sort((a, b) => b.value - a.value); // Sort descending by value
    }, [summaryData]);

    return (
        <>
            {/* First Row */}
            <Grid container columnGap={"32px"} display={"grid"} gridTemplateColumns={"1fr 2fr"} >
                <Grid display={"flex"} flexDirection={"column"} gap={"20px"} padding={"16px"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="body1" textAlign={"center"}>{period} you started prospecting</Typography>
                    <Typography variant="h4" textAlign={"center"}>{summaryData.total_accounts} Accounts</Typography>
                </Grid>
                <Grid item padding={"16px"} sx={{ border: "1px solid #000000" }}>
                    <SummaryLineChartCard 
                        title='Activation Trend' 
                        data={activationTrendData}
                        tooltipTitle="Number of activations over time"
                    />
                </Grid>
            </Grid>

            {/* Second Row */}
            <Box display={"grid"} marginTop={"20px"} columnGap={"32px"} gridTemplateColumns={"1fr 1fr"} >
                <Box padding={"16px"} gap={"20px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                    <Typography variant="h3">Prospecting Funnel</Typography>
                    <CustomFunnelChart data={summaryData} />
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
                        <SummaryBarChartCard 
                            direction='horizontal' 
                            title='Activities by Type' 
                            data={prospectingActivityData}
                        />
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
                            <Typography variant="h2">{summaryData.total_events}</Typography>
                        </Box>
                        <Box gap={"20px"} padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Opportunities Created</Typography>
                            <Typography variant="h2">{summaryData.total_deals}</Typography>
                        </Box>
                    </Box>

                    <Box display={"flex"} flex={1} flexDirection={"row"} gap={"20px"}>
                        <Box gap={"20px"} padding={"16px"} display={"flex"} flex={1} flexDirection={"column"} alignItems={"center"} sx={{ border: "1px solid #000000" }}>
                            <Typography variant="body1">Opportunity Value</Typography>
                            <Typography variant="h2">{summaryData.total_pipeline_value?.toLocaleString(undefined, { style: "currency", currency: "USD" })}</Typography>
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
                            <Typography variant="h4" textAlign={"center"}>{summaryData.avg_days_from_first_activity_to_opportunity}</Typography>
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
                            <Typography variant="h4" textAlign={"center"}>{summaryData.avg_outbound_activities_to_inbound_response}</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flex={1}>
                            <Typography>How many contacts do you approach on average, before getting a response from someone in the account?</Typography>
                        </Box>
                        <Box width={"160px"}>
                            <Typography variant="h4" textAlign={"center"}>{summaryData.avg_number_approached_contacts_to_engage}</Typography>
                        </Box>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flex={1}>
                            <Typography>What type of activity most strongly correlates with prospect responses?</Typography>
                        </Box>
                        <Tooltip title={`${(summaryData.most_effective_prospecting_activity_for_engagement_fraction * 100).toFixed(2)}% of outbound prospecting activities prior to engagement`}>
                        <Box width={"160px"}>
                            <Typography variant="h4" textAlign={"center"}>
                                    {summaryData.most_effective_prospecting_activity_for_engagement}
                                </Typography>
                            </Box>
                        </Tooltip>
                    </Box>

                    <Box padding={"16px"} display={"flex"} flex={1} flexDirection={"row"} alignItems={"center"} gap={"20px"} sx={{ border: "1px solid #000000" }}>
                        <Box display={"flex"} flex={1}>
                            <Typography>What type of activity most strongly correlates with setting a meeting?</Typography>
                        </Box>
                        <Tooltip title={`${(summaryData.most_effective_prospecting_activity_for_meeting_fraction * 100).toFixed(2)}% of outbound prospecting activities prior to setting a meeting`}>
                            <Box width={"160px"}>
                                <Typography variant="h4" textAlign={"center"}>
                                    {summaryData.most_effective_prospecting_activity_for_meeting}
                                </Typography>
                            </Box>
                        </Tooltip>
                    </Box>
                </Box>
            </Box>
        </>
    )
}

export default ProspectingSummary