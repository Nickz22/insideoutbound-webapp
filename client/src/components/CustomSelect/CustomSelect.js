import React from 'react';
import { InputLabel, MenuItem, Select } from '@mui/material';

/**
 * @param {object} props
 * @param {(e: import('@mui/material').SelectChangeEvent<string>) => void} props.onChange
 * @param {string} props.value
 * @param {string} props.label
 * @param {string} props.placeholder
 * @param {string[]} props.options
 */
const CustomSelect = (props) => {
    return (
        <>
            <InputLabel
                sx={{
                    fontSize: "16px",
                    color: "#4C4C4C",
                    fontWeight: "500",
                    margin: 0,
                    left: "-14px"
                }}
            >{props.label}</InputLabel>
            <Select
                value={props.value}
                onChange={props.onChange}
                label={props.label}
                variant='standard'
                fullWidth
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
                    }
                }}
            >
                <MenuItem value={"placeholder"} sx={{ display: "none" }}>
                    {props.placeholder}
                </MenuItem>
                {props.options.map((option, index) => (
                    <MenuItem
                        key={index}
                        value={option}
                    >
                        {option}
                    </MenuItem>
                ))}
            </Select>
        </>
    )
}

export default CustomSelect