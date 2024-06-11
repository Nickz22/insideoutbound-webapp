import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const mockData = [
  { name: "Step 1", value: 22 },
  { name: "Step 2", value: 41 },
  { name: "Step 3", value: 35 },
  { name: "Step 4", value: 12 },
];

const ConversionRatesChart = () => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={mockData}
        layout="vertical"
        margin={{
          top: 20,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis dataKey="name" type="category" />
        <Tooltip />
        <Legend />
        <Bar dataKey="value" fill="#8884d8" />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default ConversionRatesChart;
