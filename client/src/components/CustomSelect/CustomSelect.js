import React from 'react';
import { Box, InputLabel, MenuItem, Select, Tooltip } from '@mui/material';

/**
 * @param {object} props
 * @param {(e: import('@mui/material').SelectChangeEvent<string>) => void} props.onChange
 * @param {string} props.value
 * @param {string} [props.label]
 * @param {string} props.placeholder
 * @param {string[] | {value: string, label: string}[]} props.options
 * @param {Omit<import('@mui/material').TooltipProps, "children">} [props.tooltip]
 * @param {import('@mui/material').BaseSelectProps["sx"]} [props.selectSx={}]
 * @param {import('@mui/material').InputLabelOwnProps["sx"]} [props.labelSx={}]
 */
const CustomSelect = ({ onChange, value, label, placeholder, options, tooltip = undefined, selectSx = {}, labelSx = {} }) => {
    return (
        <Tooltip {...tooltip} title={tooltip?.title}>
            <Box>
                {label && label.length > 0 && (
                    <InputLabel
                        sx={{
                            fontSize: "16px",
                            color: "#4C4C4C",
                            fontWeight: "500",
                            margin: 0,
                            top: "-16px",
                            left: "-14px",
                            "&.Mui-focused": {
                                top: "0px"
                            },
                            ...labelSx
                        }}
                    >{label}</InputLabel>
                )}
                <Select
                    value={value}
                    onChange={onChange}
                    label={label}
                    variant='standard'
                    fullWidth
                    displayEmpty
                    sx={{
                        color: "rgba(83, 58, 243, 1)",
                        fontWeight: "400",
                        fontSize: "26px",
                        letterSpacing: "-0.78px",
                        borderBottom: "1px solid rgba(83, 58, 243, 1)",
                        "::before": {
                            borderBottom: "none"
                        },
                        "::after": {
                            borderBottom: "none"
                        },
                        ":hover": {
                            borderBottom: "2px solid rgba(83, 58, 243, 1)",
                        },
                        ":hover:not(.Mui-disabled, .Mui-error):before": {
                            borderBottom: "2px solid rgba(83, 58, 243, 1)",
                        },
                        ":hover::after": {
                            borderBottom: "none",
                        },
                        ...selectSx
                    }}
                >
                    <MenuItem value={""} sx={{ display: "none" }}>
                        {placeholder}
                    </MenuItem>
                    {options.map((option, index) => (
                        <MenuItem
                            key={index}
                            value={typeof option === "object" ? option.value : option}
                        >
                            {typeof option === "object" ? option.label : option}
                        </MenuItem>
                    ))}
                </Select >
            </Box>
        </Tooltip>
    )
}

export default CustomSelect