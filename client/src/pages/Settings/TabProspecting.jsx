import { Box, Button, Card, CardContent, Grid, IconButton, Typography } from '@mui/material'
import FilterContainer from 'src/components/FilterContainer/FilterContainer'
import { FILTER_OPERATOR_MAPPING } from 'src/utils/c'
import CloseIcon from "@mui/icons-material/Close";
import { useSettings } from './SettingProvider';

const REQUIRED_PROSPECTING_CATEGORIES = [
    "Call Connect",
    "Dial",
    "Inbound Email",
    "Outbound Email",
];

const TabProspecting = () => {
    const {
        criteria,
        handleCriteriaChange,
        handleDeleteFilter,
        handleAddCriteria,
        filter: {
            taskFilterFields
        }
    } = useSettings();

    return (
        <Card id="prospecting" sx={{ mb: 2 }}>
            <CardContent sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Prospecting Activity Criteria
                </Typography>
                <Grid container spacing={2}>
                    {criteria.map((criteriaContainer, index) => (
                        <Grid item xs={12} md={6} key={`criteria-${index}`}>
                            <Box sx={{ position: "relative" }}>
                                <FilterContainer
                                    isNameReadOnly={REQUIRED_PROSPECTING_CATEGORIES.includes(criteriaContainer.name)}
                                    isDirectionReadOnly={REQUIRED_PROSPECTING_CATEGORIES.includes(criteriaContainer.name)}
                                    key={`filter-${index}`}
                                    initialFilterContainer={criteriaContainer}
                                    onLogicChange={
                                        /** @param {import('types/FilterContainer').FilterContainer} newContainer */
                                        (newContainer) => {
                                            if (handleCriteriaChange) {
                                                handleCriteriaChange(index, newContainer)
                                            }
                                        }
                                    }
                                    onValueChange={
                                        /** @param {import('types/FilterContainer').FilterContainer} newContainer */
                                        (newContainer) => {
                                            if (handleCriteriaChange) {
                                                handleCriteriaChange(index, newContainer)
                                            }
                                        }
                                    }
                                    filterFields={taskFilterFields}
                                    filterOperatorMapping={FILTER_OPERATOR_MAPPING}
                                    hasNameField={true}
                                    hasDirectionField={true}
                                />
                                {
                                    !REQUIRED_PROSPECTING_CATEGORIES.includes(criteriaContainer.name) && (
                                        <IconButton
                                            aria-label="delete"
                                            onClick={() => handleDeleteFilter(index)}
                                            sx={{ position: "absolute", top: 0, right: 0 }}
                                        >
                                            <CloseIcon />
                                        </IconButton>
                                    )
                                }
                            </Box>
                        </Grid>
                    ))}
                </Grid>
                <Button variant="outlined" onClick={handleAddCriteria} sx={{ mt: 2 }}>
                    Add Criteria
                </Button>
            </CardContent>
        </Card>
    )
}

export default TabProspecting