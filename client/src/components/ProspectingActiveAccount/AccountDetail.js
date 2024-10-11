import { Box, Card, Grid, Typography } from "@mui/material"
import CustomTable from "../CustomTable/CustomTable"
import CardActiveAccount from "./CardActiveAccount"
import { Link } from "react-router-dom"
import { tableColumns } from "../../pages/Prospecting/tableColumns";
import { useState } from "react";

const AccountDetail = ({ detailedActivationData, instanceUrl, totalItems, page, rowsPerPage, handlePageChange, handleRowsPerPageChange, handleRowClick, tableLoading, handleSearch, selectedActivation }) => {
  const [columnShows, setColumnShows] = useState(
    localStorage.getItem("activationColumnShow")
      ? JSON.parse(localStorage.getItem("activationColumnShow"))
      : tableColumns
  );

  const handleColumnsChange = (newColumns) => {
    setColumnShows(newColumns);
    localStorage.setItem("activationColumnShow", JSON.stringify(newColumns));
  };

  return (
    <Box sx={{ flexGrow: 1, marginTop: 5 }}>
      <Grid container spacing={2}>
        <Grid item xs={9}>
          <Card
            sx={{
              borderRadius: '20px',
              boxShadow: '0px 0px 25px rgba(0, 0, 0, 0.1)',
              paddingX: 4,
              paddingY: 2,
              margin: 'auto',
            }}
          >
            <Typography variant="h2" align="center" sx={{
              fontFamily: 'Albert Sans',
              fontWeight: 700,
              fontSize: '24px',
              lineHeight: '22.32px',
              letterSpacing: '-3%',
              paddingTop: 2,
              paddingBottom: 1
            }}>
              Active Accounts List
            </Typography>
            <CustomTable
              tableData={{
                columns: columnShows,
                data: detailedActivationData.map((item) => ({
                  ...item,
                  "account.name": (
                    <Link
                      href={`${instanceUrl}/${item.account?.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {item.account?.name || "N/A"}
                    </Link>
                  ),
                  "opportunity.name": item.opportunity ? (
                    <Link
                      href={`${instanceUrl}/${item.opportunity.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {item.opportunity.name || "N/A"}
                    </Link>
                  ) : (
                    "N/A"
                  ),
                })),
                selectedIds: new Set(),
                availableColumns: tableColumns,
              }}
              paginationConfig={{
                type: "server-side",
                totalItems: totalItems,
                page: page,
                rowsPerPage: rowsPerPage,
                onPageChange: handlePageChange,
                onRowsPerPageChange: handleRowsPerPageChange,
              }}
              onRowClick={handleRowClick}
              onColumnsChange={handleColumnsChange}
              isLoading={tableLoading}
              onSearch={handleSearch}
            />
          </Card>
        </Grid>
        <Grid item xs={3}>
          <CardActiveAccount data={selectedActivation} />
        </Grid>
      </Grid>
    </Box>
  )
}


export default AccountDetail