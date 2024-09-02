import { ONBOARD_WIZARD_STEPS } from "src/utils/c";

/** @type {import("types/Onboard").RequiredProspectingCategory[]} */
export const REQUIRED_PROSPECTING_CATEGORIES = [
    "Inbound Call",
    "Outbound Call",
    "Inbound Email",
    "Outbound Email",
];

export const PROGRESS_STEP = [
    ...ONBOARD_WIZARD_STEPS,
    { title: "Prospecting Categories" },
    { title: "Review" },
];
