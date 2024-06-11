import React from 'react';
import {
  FunnelChart,
  Funnel,
  LabelList,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

const data = [
  { name: 'Open', value: 15 },
  { name: 'In Progress', value: 3 },
  { name: 'Closing', value: 1 },
  { name: 'Closed', value: 1 },
];

const COLORS = ['#8884d8', '#83a6ed', '#8dd1e1', '#82ca9d'];

const CustomFunnelChart = () => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <FunnelChart>
        <Tooltip />
        <Funnel
          dataKey="value"
          data={data}
          isAnimationActive
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
          <LabelList position="right" fill="#000" stroke="none" dataKey="name" />
        </Funnel>
      </FunnelChart>
    </ResponsiveContainer>
  );
};

export default CustomFunnelChart;
