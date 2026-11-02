// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Stack,
} from "@mui/material";
import SearchableDataGrid, {
  SearchableDataGridProps,
} from "./SearchableDataGrid";

/**
 * CollapsibleDataGrid component that displays a collapsible data grid with a detail dialog when you double click a row.
 *
 * @param {object} props - The properties for the component.
 * @param {React.ReactNode} [props.icon] - Optional icon to display in the header.
 * @param {string} props.title - The title of the data grid.
 * @param {GridColDef[]} props.columns - The column definitions for the data grid.
 * @param {T[]} props.rows - The rows of data to display in the data grid.
 * @param {readonly (number | { value: number; label: string; })[] | undefined} [props.pageSizeOptions] - Options for page sizes.
 * @param {number} [props.initialPageSize] - Initial page size for the data grid.
 * @param {(item: T) => Record<string, React.ReactNode> | null} props.getSelectedItemProperties - Function to get properties of the selected item.
 * @param {(row: T) => string} props.getRowId - Function to get the ID of a row.
 */
const CollapsibleDataGrid = <T extends object>({
  icon,
  title,
  rows,
  ...props
}: SearchableDataGridProps<T>) => {
  return (
    <Accordion defaultExpanded={rows.length > 0} disableGutters>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" alignItems={"center"} spacing={1}>
          {icon}
          <span>{`${title} (${rows.length})`}</span>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <SearchableDataGrid icon={icon} title={title} rows={rows} {...props} />
      </AccordionDetails>
    </Accordion>
  );
};

export default CollapsibleDataGrid;
