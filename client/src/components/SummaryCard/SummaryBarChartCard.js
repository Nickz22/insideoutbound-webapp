import React, { useEffect, useRef, useState } from 'react'
import { Box, Tooltip, Typography } from '@mui/material'
import { BarChart } from '@mui/x-charts/BarChart';


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
 * @param {'horizontal' | 'vertical'} props.direction 
 */
const SummaryBarChartCard = ({ tooltipTitle = '', data, target, title, direction }) => {
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
                        marginBottom: "0px"
                    }}
                >
                    TARGET = {target}
                </Typography>
                <BarChart
                    width={dimensions.width}
                    dataset={data}
                    sx={{ marginTop: "-20px" }}
                    yAxis={[
                        {
                            scaleType: direction === "vertical" ? 'band' : 'linear',
                            dataKey: direction === "vertical" ? 'label' : 'value',
                            colorMap: direction === "vertical" ? {
                                type: 'ordinal',
                                colors: data.map((val) => {
                                    if (val.value >= target) {
                                        return 'url(#paint0_linear_bar1)'
                                    } else {
                                        return 'rgba(217, 217, 217, 1)'
                                    }
                                })
                            } : undefined,
                            categoryGapRatio: 0.4,
                        }
                    ]} // Keep band for categorical labels
                    grid={{
                        vertical: direction === "vertical" ? true : false,
                        horizontal: direction === "horizontal" ? true : false,
                    }}

                    series={[{ dataKey: 'value' }]}
                    layout={direction === "vertical" ? "horizontal" : "vertical"}
                    xAxis={[
                        {
                            dataKey: direction === "vertical" ? "value" : "label",
                            scaleType: direction === "vertical" ? 'linear' : 'band',
                            tickMinStep: 2,
                            colorMap: direction === "horizontal" ? {
                                type: 'ordinal',
                                colors: data.map((val) => {
                                    if (val.label === "5. Unresponsive") {
                                        return 'rgba(221, 64, 64, 1)'
                                    }

                                    if (val.value >= target) {
                                        return 'url(#paint0_linear_bar1)'
                                    } else {
                                        return 'rgba(217, 217, 217, 1)'
                                    }
                                })
                            } : undefined,
                            categoryGapRatio: 0.7,
                        },
                    ]}
                >
                    <OrangeBlueGradientColorDefs />
                </BarChart>
            </Box>
        </Tooltip>
    )
};

export default SummaryBarChartCard;
