import Timeline from "./TimeLine";
import { Box, Card, Grid } from "@mui/material";
import SummaryBarChartCard from "../../components/SummaryCard/SummaryBarChartCard";

function SelectedAccount({ selectedActivation }) {
  return (
    <Box sx={{ mt: 4 }}>
      <Card
        sx={{
          borderRadius: "20px",
          boxShadow: "0px 0px 25px rgba(0, 0, 0, 0.1)",
          paddingX: 4,
          paddingY: 2,
          marginX: "auto",
          marginBottom: 4,
          paddingBottom: 4,
        }}
      >
        <Box sx={{ overflowX: "auto", width: "100%" }}>
          <Box sx={{ minWidth: "600px" }}>
            <Timeline tasks={selectedActivation.tasks} />
          </Box>
        </Box>
      </Card>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Card
            sx={{
              borderRadius: "20px",
              boxShadow: "0px 0px 25px rgba(0, 0, 0, 0.1)",
              paddingX: 4,
              paddingTop: 4,
              marginX: "auto",
              marginBottom: 4,
            }}
          >
            <Box sx={{ overflowX: "auto", width: "100%" }}>
              <Box sx={{ minWidth: "200px", height: "250px" }}>
                <SummaryBarChartCard
                  direction="horizontal"
                  title="Prospecting Metadata"
                  data={selectedActivation.prospecting_metadata.map((item) => ({
                    label: item.name,
                    value: item.total,
                  }))}
                />
              </Box>
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default SelectedAccount;
