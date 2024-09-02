import {
    createContext,
    useContext,
    useEffect,
    useState,
} from "react";
import { REQUIRED_PROSPECTING_CATEGORIES } from "./OnboardConstant";

/**
 * @typedef {import("types/Filter").Filter} Filter
 * @typedef {import("types/Onboard").GatheringResponses} GatheringResponses
 * @typedef {import("types/Onboard").CategoryFormTableData} CategoryFormTableData
 * @typedef {import("types/Onboard").OnboardContextValue} OnboardContextValue
 */

/** @type {import("types/Onboard").OnboardContextInit} */
const initOnboard = {
    step: 1,
    filters: REQUIRED_PROSPECTING_CATEGORIES.map((category) => {
        /** @type {"Inbound" | "Outbound"} */
        const direction = category.toLowerCase().includes("inbound")
            ? "Inbound"
            : "Outbound";

        /** @type {Filter[]} */
        const filters = []
        return {
            name: category,
            filters: filters,
            filterLogic: "",
            direction: direction,
        }
    }),
    gatheringResponses: {},
    isLargeDialog: false,
    isTransitioning: false,
    categoryFormTableData: {
        availableColumns: [],
        columns: [],
        data: [],
        selectedIds: new Set(),
    },
    tasks: [],
    inputValues: {
        userRole: "placeholder"
    }
};

/** @type {import("react").Context<OnboardContextValue>} */
const OnboardContext = createContext(/** @type {OnboardContextValue} */(initOnboard));

/**
 * @param {{children: React.ReactNode}} props
 */
export const OnboardProvider = ({
    children,
}) => {
    const [step, setStep] = useState(initOnboard.step);
    const [filters, setFilters] = useState(initOnboard.filters);

    const [gatheringResponses, setGatheringResponses] = useState(initOnboard.gatheringResponses);
    const [isLargeDialog, setIsLargeDialog] = useState(initOnboard.isLargeDialog);
    const [isTransitioning, setIsTransitioning] = useState(initOnboard.isTransitioning);

    const [categoryFormTableData, setCategoryFormTableData] = useState(initOnboard.categoryFormTableData);

    const [tasks, setTasks] = useState(initOnboard.tasks);

    const [inputValues, setInputValues] = useState(initOnboard.inputValues);

    // const taskSObjectFields = useRef([]);
    // const taskFilterFields = useRef([]);

    /**
     * @param {number} clickedStep
     */
    const handleStepClick = (clickedStep) => {
        if (clickedStep < step) {
            setStep(clickedStep);
        }
    };

    useEffect(() => {
        const setInitialCategoryFormTableData = async () => {
            // taskSObjectFields.current =
            //     taskSObjectFields.current.length > 0
            //         ? taskSObjectFields.current
            //         : (await fetchTaskFields()).data.map(
            //             /** @param {SObjectField} field */
            //             (field) => ({
            //                 id: field.name,
            //                 label: field.label,
            //                 dataType: field.type,
            //             })
            //         );
            // setCategoryFormTableData({
            //     availableColumns: taskSObjectFields.current,
            //     columns:
            //         categoryFormTableData.columns.length > 0
            //             ? categoryFormTableData.columns
            //             : [
            //                 {
            //                     id: "select",
            //                     label: "Select",
            //                     dataType: "select",
            //                 },
            //                 {
            //                     id: "Subject",
            //                     label: "Subject",
            //                     dataType: "string",
            //                 },
            //                 {
            //                     id: "Status",
            //                     label: "Status",
            //                     dataType: "string",
            //                 },
            //                 {
            //                     id: "TaskSubtype",
            //                     label: "TaskSubtype",
            //                     dataType: "string",
            //                 },
            //             ],
            //     data: tasks,
            //     selectedIds: new Set(),
            // });
        };
        setInitialCategoryFormTableData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tasks]);

    useEffect(() => {
        const setTaskFilterFields = async () => {
            // taskFilterFields.current =
            //     taskFilterFields.current.length > 0
            //         ? taskFilterFields.current
            //         : (await fetchTaskFilterFields()).data;
        };
        setTaskFilterFields();
    }, []);

    return (
        <OnboardContext.Provider
            value={{
                filters: filters,
                step: step,
                gatheringResponses: gatheringResponses,
                isLargeDialog: isLargeDialog,
                isTransitioning: isTransitioning,
                categoryFormTableData: categoryFormTableData,
                tasks: tasks,
                inputValues,
                setFilters: setFilters,
                setStep,
                setGatheringResponses,
                setIsLargeDialog,
                setIsTransitioning,
                setCategoryFormTableData,
                setTasks,
                handleStepClick,
                setInputValues
            }}
        >
            {children}
        </OnboardContext.Provider>
    );
};

export const useOnboard = () => {
    const context = useContext(OnboardContext);
    if (!context) {
        throw new Error(
            "useOnboard must be used within a OnboardProvider"
        );
    }
    return context;
};
