import { Box, Card, CardContent, Grid, MenuItem, Select, Typography } from '@mui/material'
import FilterContainer from 'src/components/FilterContainer/FilterContainer'
import { FILTER_OPERATOR_MAPPING } from 'src/utils/c'
import { useSettings } from './SettingProvider'
import { debounce } from 'lodash'

const TabMeeting = () => {
    const { settings, handleChange, filter: { eventFilterFields, taskFilterFields } } = useSettings();

    const debounceValueChange = debounce((fieldName, newContainer) => {
        handleChange(fieldName, newContainer)
    }, 50)


    return (
        <Card id="meeting">
            <CardContent sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Meeting Criteria
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <Select
                            fullWidth
                            value={settings.meetingObject}
                            onChange={(e) => handleChange("meetingObject", e.target.value)}
                            label="Meeting Object"
                        >
                            <MenuItem value="Task">Task</MenuItem>
                            <MenuItem value="Event">Event</MenuItem>
                        </Select>
                    </Grid>
                </Grid>
                <Box sx={{ mt: 2 }}>
                    <FilterContainer
                        hasNameField={false}
                        isNameReadOnly={false}
                        initialFilterContainer={settings.meetingsCriteria}
                        onLogicChange={
                            /** @param {import('types/FilterContainer').FilterContainer} newContainer */
                            (newContainer) =>
                                handleChange("meetingsCriteria", newContainer)
                        }
                        onValueChange={
                            /** @param {import('types/FilterContainer').FilterContainer} newContainer */
                            (newContainer) => debounceValueChange("meetingsCriteria", newContainer)
                        }
                        filterFields={
                            settings.meetingObject === "Event"
                                ? eventFilterFields
                                : taskFilterFields
                        }
                        filterOperatorMapping={FILTER_OPERATOR_MAPPING}
                        hasDirectionField={false}
                    />
                </Box>
            </CardContent>
        </Card>
    )
}

export default TabMeeting