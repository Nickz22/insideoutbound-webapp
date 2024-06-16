import React, { useState } from "react";
import {
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Checkbox,
} from "@mui/material";

const ProspectingCategoryForm = ({ tasks, onAddCategory }) => {
  const [categoryName, setCategoryName] = useState("");
  const [selectedTasks, setSelectedTasks] = useState(new Set());

  const handleTaskToggle = (task) => {
    const newSelectedTasks = new Set(selectedTasks);
    if (newSelectedTasks.has(task.id)) {
      newSelectedTasks.delete(task.id);
    } else {
      newSelectedTasks.add(task.id);
    }
    setSelectedTasks(newSelectedTasks);
  };

  const handleCreateCategory = () => {
    if (categoryName.trim() === "") {
      alert("Please enter a category name.");
      return;
    }
    onAddCategory(categoryName, Array.from(selectedTasks));
    setCategoryName("");
    setSelectedTasks(new Set());
  };

  return (
    <div>
      <TextField
        label="Category"
        value={categoryName}
        onChange={(e) => setCategoryName(e.target.value)}
        placeholder="Outbound Calls"
        fullWidth
        margin="normal"
      />
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Subject</TableCell>
            <TableCell>Who</TableCell>
            <TableCell>Priority</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Task Subtype</TableCell>
            <TableCell>Select</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {tasks.map((task) => (
            <TableRow key={task.id}>
              <TableCell>{task.subject}</TableCell>
              <TableCell>{task.who}</TableCell>
              <TableCell>{task.priority}</TableCell>
              <TableCell>{task.status}</TableCell>
              <TableCell>{task.type}</TableCell>
              <TableCell>{task.taskSubtype}</TableCell>
              <TableCell>
                <Checkbox
                  checked={selectedTasks.has(task.id)}
                  onChange={() => handleTaskToggle(task)}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div style={{ marginTop: 20 }}>
        <Button
          onClick={handleCreateCategory}
          variant="contained"
          color="primary"
        >
          Create New
        </Button>
      </div>
    </div>
  );
};

export default ProspectingCategoryForm;
