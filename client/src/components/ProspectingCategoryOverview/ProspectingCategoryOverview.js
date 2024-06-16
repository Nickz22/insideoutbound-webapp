import React from "react";
import { Card, CardContent, Typography } from "@mui/material";

const CategoryOverview = ({ categories }) => {
  return (
    <div>
      {Array.from(categories.entries()).map(([category, tasks], index) => (
        <Card key={index}>
          <CardContent>
            <Typography variant="h6">{category}</Typography>
            {/* Display tasks or other relevant information */}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default CategoryOverview;
