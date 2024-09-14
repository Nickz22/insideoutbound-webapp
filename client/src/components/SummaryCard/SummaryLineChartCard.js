import React, { useEffect, useRef, useState } from 'react'
import { Box, Tooltip, Typography } from '@mui/material'
import { LineChart, lineElementClasses } from '@mui/x-charts';


const OrangeBlueGradientColorDefs = () => {
    return (
        <>
            <defs>
                <linearGradient
                    id="paint0_linear_bar1"
                    gradientTransform="rotate(0)"
                    x1="0%"
                    y1="100%"
                    x2="131%"
                    y2="0%"
                >
                    <stop offset="0%" stopColor="#FF7D2F" />
                    <stop offset="100%" stopColor="#491EFF" />
                </linearGradient>
            </defs>
        </>
    );
};

/**
 * @param {object} props
 * @param {string} [props.tooltipTitle = ''] 
 * @param {any[]} props.data 
 * @param {number} props.target 
 * @param {string} props.title
 */
const SummaryLineChartCard = ({ tooltipTitle = '', data, target, title }) => {
    const textRef = useRef(null)
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

    useEffect(() => {
        if (textRef.current) {
            const { offsetWidth, offsetHeight } = textRef.current;
            setDimensions({ width: offsetWidth, height: offsetHeight });
        }
    }, [textRef]);

    return (
        <Tooltip title={tooltipTitle} arrow>
            <Box
                sx={{
                    borderRadius: "49px",
                    padding: "34px 8px 34px 34px",
                    textAlign: "center",
                    minWidth: "150px",
                    height: "379px",
                    width: "100%",
                    boxSizing: "border-box",
                    boxShadow: "0px 2px 4px rgba(0,0,0,0.1)",
                }}
            >
                <Typography
                    ref={textRef}
                    variant='body1'
                    sx={{
                        fontSize: "24px",
                        letterSpacing: "-0.72px",
                        color: "rgba(30, 36, 47, 1)",
                        textAlign: "center",
                        fontWeight: "700",
                        lineHeight: "1",
                        marginBottom: "8px"
                    }}
                >
                    {title}
                </Typography>
                <Typography
                    variant='body1'
                    sx={{
                        fontSize: "12px",
                        letterSpacing: "2.4px",
                        color: "rgba(30, 36, 47, 1)",
                        textAlign: "center",
                        fontWeight: "500",
                        lineHeight: "1",
                        marginBottom: "8px"
                    }}
                >
                    TARGET = {target}
                </Typography>
                <LineChart
                    width={dimensions.width}
                    dataset={data}
                    sx={{
                        [`& .${lineElementClasses.root}`]: {
                            strokeWidth: 2,
                            stroke: 'url(#paint0_linear_bar1)'
                        },
                        marginTop: "-20px"
                    }}
                    grid={{ horizontal: true }}
                    yAxis={[
                        {
                            fill: 'url(#paint0_linear_bar1)',
                            scaleType: 'linear',
                            dataKey: 'value',
                        }
                    ]}

                    series={[{ dataKey: 'value', color: 'url(#paint0_linear_bar1)' }]}
                    xAxis={[
                        {
                            dataKey: "label",
                            scaleType: "band",
                            colorMap: {
                                type: 'ordinal',
                                colors: data.map(() => {
                                    return 'url(#paint0_linear_bar1)'
                                })
                            }
                        },
                    ]}
                >
                    <OrangeBlueGradientColorDefs />
                </LineChart>
            </Box>
        </Tooltip>
    )
};

export default SummaryLineChartCard;
