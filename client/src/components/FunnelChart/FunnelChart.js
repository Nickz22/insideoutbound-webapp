import React from 'react';
import {
  FunnelChart,
  Funnel,
  LabelList,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

const COLORS = ['#8884d8', '#83a6ed', '#8dd1e1', '#82ca9d'];

const CustomFunnelChart = ({ data }) => {
  const funnelData = [
    { name: 'Activated', value: data.in_status_activated },
    { name: 'Engaged', value: data.in_status_engaged },
    { name: 'Meeting Set', value: data.in_status_meeting_set },
    { name: 'Opportunity', value: data.in_status_opportunity_created },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <FunnelChart>
        <Tooltip />
        <Funnel
          dataKey="value"
          data={funnelData}
          isAnimationActive
        >
          {funnelData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
          <LabelList position="right" fill="#000" stroke="none" dataKey="name" />
          <LabelList position="center" fill="#fff" stroke="none" dataKey="value" />
        </Funnel>
      </FunnelChart>
    </ResponsiveContainer>
  );
};

export default CustomFunnelChart;
