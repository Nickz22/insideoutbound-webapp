import React, { useState } from "react";

const InfoGatheringStep = ({ stepData, onComplete }) => {
  const [inputValue, setInputValue] = useState("");

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
  };

  const handleSubmit = () => {
    onComplete([{ label: stepData.setting, value: inputValue }]);
  };

  const renderInput = () => {
    switch (stepData.inputType) {
      case "text":
        return (
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder={stepData.inputLabel}
            className="w-full p-2 border rounded"
          />
        );
      case "number":
        return (
          <input
            type="number"
            value={inputValue}
            onChange={handleInputChange}
            placeholder={stepData.inputLabel}
            className="w-full p-2 border rounded"
          />
        );
      case "picklist":
        return (
          <select
            value={inputValue}
            onChange={handleInputChange}
            className="w-full p-2 border rounded"
          >
            <option value="">Select an option</option>
            {stepData.options.map((option, index) => (
              <option key={index} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">{stepData.title}</h2>
      <p className="mb-4">{stepData.description}</p>
      <div className="mb-4">{renderInput()}</div>
      <button
        onClick={handleSubmit}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Next
      </button>
    </div>
  );
};

export default InfoGatheringStep;
