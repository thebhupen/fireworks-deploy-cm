// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import SearchIcon from "@mui/icons-material/Search";
import { FormControl, Stack, TextField } from "@mui/material";
import {
  DataGrid,
  GridColDef,
  GridRowSelectionModel,
  GridSortModel,
} from "@mui/x-data-grid";
import * as React from "react";
import { useMemo, useState } from "react";
import DetailsDialog from "../DetailsDialog";

const ROW_HEIGHT = 28;

export interface SearchableDataGridProps<T extends object> {
  icon?: React.ReactNode;
  title: string;
  columns: GridColDef[];
  rows: T[];
  getSelectedItemTitle?: (item: T) => React.ReactNode | null;
  getSelectedItemProperties?: (
    item: T,
  ) => Record<string, React.ReactNode> | null;
  getSelectedItemContent?: (item: T) => React.ReactNode | null;
  getSelectedItemActions?: (item: T) => React.ReactNode | null;
  getRowId: (row: T) => string;
  pageSizeOptions?:
    | readonly (
        | number
        | {
            value: number;
            label: string;
          }
      )[]
    | undefined;
  initialPageSize?: number;
  initialSortModel?: GridSortModel;
  searchFn?: (rows: T[], searchTerm: string) => T[];
  isLoading?: boolean;
  onRowSelection?: (rowId: string | null) => void;
  enableAutoRowHeight?: boolean;
}

const DEFAULT_PAGE_SIZE_OPTIONS = [10, 25, 50, 100];
const DEFAULT_PAGE_SIZE = 10;

/**
 * SearchableDataGrid component that displays a collapsible data grid with a detail dialog when you double click a row.
 *
 * @param {object} props - The properties for the component.
 * @param {React.ReactNode} [props.icon] - Optional icon to display in the header.
 * @param {string} props.title - The title of the data grid.
 * @param {GridColDef[]} props.columns - The column definitions for the data grid.
 * @param {T[]} props.rows - The rows of data to display in the data grid.
 * @param {readonly (number | { value: number; label: string; })[] | undefined} [props.pageSizeOptions] - Options for page sizes.
 * @param {number} [props.initialPageSize] - Initial page size for the data grid.
 * @param {(item: T) => React.ReactNode | null} [props.getSelectedItemTitle] - Optional function to get title of the selected item.
 * @param {(item: T) => Record<string, React.ReactNode> | null} props.getSelectedItemProperties - Function to get properties of the selected item.
 * @param {(item: T) => React.ReactNode | null} [props.getSelectedItemContent] - Optional function to get content of the selected item.
 * @param {(item: T) => React.ReactNode | null} [props.getSelectedItemActions] - Optional function to get actions of the selected item.
 * @param {(row: T) => string} props.getRowId - Function to get the ID of a row.
 * @param {GridSortModel} [props.initialSortModel] - Initial sort model for the data grid.
 * @param {(rows: T[], searchTerm: string) => T[]} [props.searchFn] - Optional function to search the rows.
 */
const SearchableDataGrid = <T extends object>({
  icon,
  title,
  columns,
  rows,
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
  initialPageSize = DEFAULT_PAGE_SIZE,
  initialSortModel,
  isLoading,
  enableAutoRowHeight = false,
  getSelectedItemTitle,
  getSelectedItemProperties,
  getSelectedItemContent,
  getSelectedItemActions,
  getRowId,
  searchFn,
  onRowSelection,
}: SearchableDataGridProps<T>) => {
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [selectedItemTitle, setSelectedItemTitle] =
    useState<React.ReactNode | null>(null);
  const [selectedItemProperties, setSelectedItemProperties] = useState<Record<
    string,
    React.ReactNode
  > | null>(null);
  const [selectedItemContent, setSelectedItemContent] =
    useState<React.ReactNode | null>(null);
  const [selectedItemActions, setSelectedItemActions] =
    useState<React.ReactNode | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [rowSelectionModel, setRowSelectionModel] =
    React.useState<GridRowSelectionModel>({ type: "include", ids: new Set() });

  /**
   * Handles the double-click event on a row.
   *
   * @param {T} item - The item that was double-clicked.
   */
  const handleRowDoubleClick = (item: T) => {
    setSelectedItemId(getRowId(item));
    setSelectedItemTitle(
      getSelectedItemTitle ? getSelectedItemTitle(item) : null,
    );
    setSelectedItemProperties(
      getSelectedItemProperties ? getSelectedItemProperties(item) : null,
    );
    setSelectedItemContent(
      getSelectedItemContent ? getSelectedItemContent(item) : null,
    );
    setSelectedItemActions(
      getSelectedItemActions ? getSelectedItemActions(item) : null,
    );
  };

  /**
   * Closes the details dialog.
   */
  const handleClose = () => {
    setSelectedItemId(null);
    setSelectedItemTitle(null);
    setSelectedItemProperties(null);
    setSelectedItemContent(null);
    setSelectedItemActions(null);
  };

  /**
   * Filters the rows based on the search term.
   *
   * @returns {T[]} The filtered rows.
   */
  const filteredRows = useMemo(() => {
    return searchFn
      ? searchFn(rows, searchTerm)
      : rows.filter((row) => {
          if (row === null || row === undefined) {
            return false;
          }
          return Object.values(row).some((value) =>
            (value ?? "")
              .toString()
              .toLowerCase()
              .includes(searchTerm.toLowerCase()),
          );
        });
  }, [rows, searchTerm, searchFn]);

  return (
    <>
      {(!!selectedItemProperties || !!selectedItemContent) && (
        <DetailsDialog
          icon={selectedItemTitle ? null : icon}
          properties={selectedItemProperties}
          content={selectedItemContent}
          actions={selectedItemActions}
          isOpen
          onClose={handleClose}
          title={selectedItemTitle ?? selectedItemId ?? `${title} Details`}
        />
      )}
      <Stack spacing={1}>
        <FormControl fullWidth>
          <TextField
            placeholder={`Search ${title}...`}
            onChange={(e) => setSearchTerm(e.target.value)}
            slotProps={{
              input: {
                startAdornment: <SearchIcon />,
              },
            }}
            size="small"
          />
        </FormControl>
        <DataGrid
          columns={columns}
          rows={filteredRows}
          getRowId={getRowId}
          onRowDoubleClick={
            handleRowDoubleClick
              ? (params) => handleRowDoubleClick(params.row)
              : undefined
          }
          pageSizeOptions={pageSizeOptions}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: initialPageSize,
              },
            },
            sorting: {
              sortModel: initialSortModel,
            },
          }}
          rowHeight={ROW_HEIGHT}
          density="compact"
          getRowHeight={enableAutoRowHeight ? () => "auto" : undefined}
          loading={isLoading}
          onRowSelectionModelChange={(newRowSelectionModel) => {
            if (onRowSelection) {
              const selectedIds = Array.isArray(newRowSelectionModel)
                ? newRowSelectionModel
                : Object.keys(newRowSelectionModel);
              onRowSelection(
                selectedIds.length > 0 ? `${selectedIds[0]}` : null,
              );
            }
            setRowSelectionModel(newRowSelectionModel);
          }}
          rowSelectionModel={rowSelectionModel}
        />
      </Stack>
    </>
  );
};

export default SearchableDataGrid;
