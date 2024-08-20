import { Box, Card, CardContent, CircularProgress, Grid, MenuItem, Select, Typography } from '@mui/material';
import { useSettings } from './SettingProvider';
import CustomTable from 'src/components/CustomTable/CustomTable';

const TabUserRole = () => {
    const {
        settings,
        status: {
            isTableLoading,
        },
        handleChange,
        tableData,
        handleTableSelectionChange,
        handleColumnsChange
    } = useSettings();

    return (
        <Card id="user-role" sx={{ mb: 2 }}>
            <CardContent sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom marginBottom={2}>
                    User Role and Team Members
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <Select
                            fullWidth
                            value={settings.userRole}
                            onChange={(e) => handleChange("userRole", e.target.value)}
                            label="User Role"
                        >
                            <MenuItem value="I manage a team">I manage a team</MenuItem>
                            <MenuItem value="I am an individual contributor">
                                I am an individual contributor
                            </MenuItem>
                        </Select>
                    </Grid>
                </Grid>
                {settings.userRole === "I manage a team" && (
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle1" gutterBottom>
                            Select Team Members
                        </Typography>
                        {isTableLoading ? (
                            <CircularProgress />
                        ) : (
                            tableData && (
                                <CustomTable
                                    onRowClick={() => { return; }}
                                    tableData={tableData}
                                    onSelectionChange={handleTableSelectionChange}
                                    onColumnsChange={handleColumnsChange}
                                    paginate={true}
                                />
                            )
                        )}
                    </Box>
                )}
            </CardContent>
        </Card>
    )
}

export default TabUserRole;