// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { useState } from "react";
import {
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Chip,
  Paper,
  Stack,
  IconButton,
  Button,
  Divider,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";

type ParamType = {
  type: string;
  has_default: boolean | string;
  default: any;
  description: string;
  example: any;
};

// Interface for list items in the form
interface ListItem {
  id: string;
  value: any;
}

// Interface for dictionary entries in the form
interface DictEntry {
  id: string;
  key: string;
  value: any;
}

// Helper function to determine if a parameter is required
function isRequired(param: ParamType): boolean {
  const typeStr = String(param.type).toLowerCase();
  return !typeStr.includes("optional") && param.default === null;
}

// Helper function to get a clean type name
function getCleanTypeName(param: ParamType): string {
  const typeStr = String(param.type);
  if (typeStr.includes("Optional[")) {
    // Find the matching closing bracket for Optional
    const optionalStart = typeStr.indexOf("Optional[");
    if (optionalStart !== -1) {
      let bracketCount = 0;
      let i = optionalStart + "Optional[".length;

      // Find the matching closing bracket
      while (i < typeStr.length) {
        if (typeStr[i] === "[") {
          bracketCount++;
        } else if (typeStr[i] === "]") {
          if (bracketCount === 0) {
            // Found the matching closing bracket
            const innerType = typeStr.substring(
              optionalStart + "Optional[".length,
              i,
            );
            const prefix = typeStr.substring(0, optionalStart);
            const suffix = typeStr.substring(i + 1);
            return prefix + innerType + suffix;
          }
          bracketCount--;
        }
        i++;
      }
    }
  }
  return typeStr;
}

// Helper function to check if a parameter is a list type
function isList(param: ParamType): boolean {
  const typeStr = String(param.type).toLowerCase();
  return typeStr.includes("list") || typeStr.includes("array");
}

// Helper function to check if a parameter is a dictionary type
function isDict(param: ParamType): boolean {
  const typeStr = String(param.type).toLowerCase();
  return (
    typeStr.includes("dict") ||
    typeStr.includes("map") ||
    typeStr.includes("object")
  );
}

// Helper function to extract the inner type of a list
function getListInnerType(param: ParamType): string {
  const typeStr = String(param.type);
  const match =
    typeStr.match(/List\[(.*?)\]/i) || typeStr.match(/Array\[(.*?)\]/i);
  return match ? match[1] : "str";
}

// Helper function to extract the value type of a dictionary
function getDictValueType(param: ParamType): string {
  const typeStr = String(param.type);
  const match =
    typeStr.match(/Dict\[.*?,\s*(.*?)\]/i) ||
    typeStr.match(/Map\[.*?,\s*(.*?)\]/i);
  return match ? match[1] : "Any";
}

function valueInputType(valueType: string): string {
  if (
    valueType.toLowerCase() === "int" ||
    valueType.toLowerCase() === "float"
  ) {
    return "number";
  }
  return "text";
}

/**
 * ListField component for handling list type parameters
 */
interface ListFieldProps {
  paramName: string;
  param: ParamType;
  innerType: string;
  required: boolean;
  value?: any[];
  onChange?: (value: any[]) => void;
}

function ListField({
  paramName,
  param,
  innerType,
  required,
  value = [],
  onChange,
}: ListFieldProps): React.ReactNode {
  const [items, setItems] = useState<ListItem[]>(
    value.length > 0
      ? value.map((val, index) => ({ id: String(index), value: val }))
      : [{ id: "0", value: "" }],
  );

  const addItem = () => {
    const newId = String(items.length);
    const newItems = [...items, { id: newId, value: "" }];
    setItems(newItems);

    if (onChange) {
      onChange(newItems.map((item) => item.value));
    }
  };

  const removeItem = (id: string) => {
    const newItems = items.filter((item) => item.id !== id);
    setItems(newItems);

    if (onChange) {
      onChange(newItems.map((item) => item.value));
    }
  };

  const handleItemChange = (id: string, value: any) => {
    const newItems = items.map((item) =>
      item.id === id ? { ...item, value } : item,
    );
    setItems(newItems);

    if (onChange) {
      onChange(newItems.map((item) => item.value));
    }
  };

  return (
    <Box sx={{ mt: 2, mb: 1 }}>
      <Typography variant="subtitle2" gutterBottom>
        {paramName} (List of {innerType})
      </Typography>

      {items.map((item) => (
        <Box
          key={item.id}
          sx={{ display: "flex", alignItems: "center", mb: 1 }}
        >
          <TextField
            fullWidth
            size="small"
            type={valueInputType(innerType)}
            value={item.value}
            onChange={(e) => handleItemChange(item.id, e.target.value)}
            placeholder={`${innerType} value`}
            required={required}
          />
          <IconButton
            color="error"
            onClick={() => removeItem(item.id)}
            disabled={items.length <= 1}
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      ))}

      <Button
        startIcon={<AddIcon />}
        onClick={addItem}
        variant="outlined"
        size="small"
        sx={{ mt: 1 }}
      >
        Add Item
      </Button>

      <FormHelperText>{param.description}</FormHelperText>
    </Box>
  );
}

/**
 * DictField component for handling dictionary type parameters
 */
interface DictFieldProps {
  paramName: string;
  param: ParamType;
  valueType: string;
  required: boolean;
  value?: Record<string, any>;
  onChange?: (value: Record<string, any>) => void;
}

function DictField({
  paramName,
  param,
  valueType,
  required,
  value = {},
  onChange,
}: DictFieldProps): React.ReactNode {
  const initialEntries =
    Object.keys(value).length > 0
      ? Object.entries(value).map(([key, val], index) => ({
          id: String(index),
          key,
          value: val,
        }))
      : [{ id: "0", key: "", value: "" }];

  const [entries, setEntries] = useState<DictEntry[]>(initialEntries);

  const updateParentValue = (newEntries: DictEntry[]) => {
    if (onChange) {
      const dictValue = newEntries.reduce(
        (acc, entry) => {
          if (entry.key) {
            acc[entry.key] = entry.value;
          }
          return acc;
        },
        {} as Record<string, any>,
      );

      onChange(dictValue);
    }
  };

  const addEntry = () => {
    const newId = String(entries.length);
    const newEntries = [...entries, { id: newId, key: "", value: "" }];
    setEntries(newEntries);
    updateParentValue(newEntries);
  };

  const removeEntry = (id: string) => {
    const newEntries = entries.filter((entry) => entry.id !== id);
    setEntries(newEntries);
    updateParentValue(newEntries);
  };

  const handleKeyChange = (id: string, key: string) => {
    const newEntries = entries.map((entry) =>
      entry.id === id ? { ...entry, key } : entry,
    );
    setEntries(newEntries);
    updateParentValue(newEntries);
  };

  const handleValueChange = (id: string, value: any) => {
    const newEntries = entries.map((entry) =>
      entry.id === id ? { ...entry, value } : entry,
    );
    setEntries(newEntries);
    updateParentValue(newEntries);
  };

  return (
    <Box sx={{ mt: 2, mb: 1 }}>
      <Typography variant="subtitle2" gutterBottom>
        {paramName} (Dictionary with {valueType} values)
      </Typography>

      {entries.map((entry) => (
        <Box key={entry.id} sx={{ mb: 2 }}>
          <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
            <TextField
              sx={{ mr: 1, flex: 1 }}
              size="small"
              label="Key"
              value={entry.key}
              onChange={(e) => handleKeyChange(entry.id, e.target.value)}
              required={required}
            />
            <TextField
              sx={{ flex: 2 }}
              size="small"
              label="Value"
              type={valueInputType(valueType)}
              value={entry.value}
              onChange={(e) => handleValueChange(entry.id, e.target.value)}
              required={required}
            />
            <IconButton
              color="error"
              onClick={() => removeEntry(entry.id)}
              disabled={entries.length <= 1}
            >
              <DeleteIcon />
            </IconButton>
          </Box>
          {entry.id !== entries[entries.length - 1].id && (
            <Divider sx={{ my: 1 }} />
          )}
        </Box>
      ))}

      <Button
        startIcon={<AddIcon />}
        onClick={addEntry}
        variant="outlined"
        size="small"
        sx={{ mt: 1 }}
      >
        Add Entry
      </Button>

      <FormHelperText>{param.description}</FormHelperText>
    </Box>
  );
}

interface ParamInputFieldProps {
  paramName: string;
  param: ParamType;
  readOnly?: boolean;
  value?: any;
  onChange?: (value: any) => void;
}

/**
 * ParamInputField component renders the appropriate input field based on parameter type
 */
function ParamInputField({
  paramName,
  param,
  readOnly = false,
  value,
  onChange,
}: ParamInputFieldProps): React.ReactNode {
  const cleanType = getCleanTypeName(param);
  const required = isRequired(param);

  // If in read-only mode, just show parameter information without interactive elements
  if (readOnly) {
    return (
      <Box sx={{ mt: 1 }}>
        <Typography variant="body2" sx={{ mb: 1 }}>
          {param.description}
        </Typography>
        {param.example !== null && (
          <Typography variant="caption" color="text.secondary" display="block">
            Example: {String(param.example)}
          </Typography>
        )}
        {param.default !== null && (
          <Typography variant="caption" color="text.secondary" display="block">
            Default: {String(param.default)}
          </Typography>
        )}
      </Box>
    );
  }

  // Handle list type parameters
  if (isList(param)) {
    const innerType = getListInnerType(param);
    return (
      <ListField
        paramName={paramName}
        param={param}
        innerType={innerType}
        required={required}
        value={value}
        onChange={onChange}
      />
    );
  }

  // Handle dictionary type parameters
  if (isDict(param)) {
    const valueType = getDictValueType(param);
    return (
      <DictField
        paramName={paramName}
        param={param}
        valueType={valueType}
        required={required}
        value={value}
        onChange={onChange}
      />
    );
  }

  // For parameters with specific options mentioned in the description
  if (
    param.description &&
    param.description.includes("(") &&
    param.description.includes(")")
  ) {
    const optionsMatch = param.description.match(/\(([^)]+)\)/);
    if (optionsMatch) {
      const options = optionsMatch[1].split(", ");

      return (
        <FormControl fullWidth margin="normal" required={required}>
          <InputLabel id={`${paramName}-label`}>{paramName}</InputLabel>
          <Select
            labelId={`${paramName}-label`}
            id={paramName}
            label={paramName}
            value={value || ""}
            onChange={(e) => onChange?.(e.target.value)}
          >
            {options.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
          <FormHelperText>{param.description}</FormHelperText>
        </FormControl>
      );
    }
  }

  const inputType = valueInputType(cleanType);

  return (
    <TextField
      fullWidth
      id={paramName}
      label={paramName}
      type={inputType}
      margin="normal"
      required={required}
      helperText={param.description}
      value={value || ""}
      onChange={(e) => {
        const newValue =
          inputType === "number"
            ? e.target.value === ""
              ? ""
              : Number(e.target.value)
            : e.target.value;
        onChange?.(newValue);
      }}
    />
  );
}

type ToolParamsFormProps = {
  params: Record<string, ParamType>;
  values?: Record<string, any>;
  onChange?: (name: string, value: any) => void;
  readOnly?: boolean;
};

/**
 * ToolParamsForm component displays tool parameters in a form-like format
 * using Material UI components instead of showing them as JSON.
 *
 * @param params - The tool parameters to display
 * @param values - Current values for the parameters
 * @param onChange - Callback function called when parameter values change
 * @returns React component displaying tool parameters in a form-like format
 */
function ToolParamsForm({
  params,
  values = {},
  onChange,
  readOnly = false,
}: ToolParamsFormProps): React.ReactNode {
  if (!params || Object.keys(params).length === 0) {
    return (
      <Typography variant="body2">
        This tool doesn't require any parameters
      </Typography>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      <Stack spacing={2}>
        {Object.entries(params).map(([paramName, param]) => (
          <Paper elevation={1} sx={{ p: 2 }} key={paramName}>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}
            >
              <Typography variant="subtitle1" fontWeight="bold">
                {paramName}
              </Typography>
              <Box>
                <Chip
                  label={getCleanTypeName(param)}
                  color="primary"
                  size="small"
                  sx={{ mr: 1 }}
                />
                {isRequired(param) ? (
                  <Chip label="Required" color="error" size="small" />
                ) : (
                  <Chip label="Optional" color="default" size="small" />
                )}
              </Box>
            </Box>

            <ParamInputField
              paramName={paramName}
              param={param}
              readOnly={readOnly}
              value={values[paramName]}
              onChange={(value) => onChange?.(paramName, value)}
            />

            {!readOnly && param.example !== null && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Example: {String(param.example)}
                </Typography>
              </Box>
            )}

            {!readOnly && param.default !== null && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Default: {String(param.default)}
                </Typography>
              </Box>
            )}
          </Paper>
        ))}
      </Stack>
    </Box>
  );
}

export default ToolParamsForm;
