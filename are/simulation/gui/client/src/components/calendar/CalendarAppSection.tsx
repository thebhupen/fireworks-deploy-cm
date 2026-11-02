// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ViewListIcon from "@mui/icons-material/ViewList";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
} from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import React, { useMemo, useState } from "react";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import SearchableDataGrid from "../common/datagrid/SearchableDataGrid";
import FullCalendarView from "./FullCalendarView";
import { CalendarEvent } from "./types";

type EventsView = "calendar" | "table";

function CalendarAppSection({
  data = {},
}: {
  data: Record<string, CalendarEvent>;
}): React.ReactNode {
  const [view, setView] = useState<EventsView>("calendar");
  const events = useMemo(() => Object.values(data), [data]);
  const changeView = (
    event: React.MouseEvent<HTMLElement>,
    value: EventsView,
  ) => {
    event.stopPropagation();
    setView(value);
  };

  const columns: GridColDef[] = [
    {
      field: "start_datetime",
      headerName: "Start Time",
      renderCell: (params) => formatDateAndTimeFromTime(params.value * 1000),
      width: 200,
    },
    {
      field: "end_datetime",
      headerName: "End Time",
      renderCell: (params) => formatDateAndTimeFromTime(params.value * 1000),
      width: 200,
    },
    { field: "title", headerName: "Title", width: 200 },
    {
      field: "attendees",
      headerName: "Attendees",
      renderCell: (params) => params.value.join(", "),
      width: 150,
    },
    { field: "tag", headerName: "Tag" },
    { field: "location", headerName: "Location", width: 200 },
  ];

  const getSelectedItemProperties = (event: CalendarEvent) => ({
    ID: event.event_id,
    Title: event.title,
    Description: event.description,
    "Start Time": formatDateAndTimeFromTime(event.start_datetime * 1000),
    "End Time": formatDateAndTimeFromTime(event.end_datetime * 1000),
    Tag: event.tag,
    Location: event.location,
    Attendees: event.attendees.join(", "),
  });

  return (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack
          direction="row"
          alignItems={"center"}
          justifyContent={"space-between"}
          width={1}
          paddingRight={2}
        >
          <Stack direction="row" spacing={1}>
            <CalendarMonthIcon />
            <span>{`Events (${events.length})`}</span>
          </Stack>
          <ToggleButtonGroup
            value={view}
            exclusive
            onChange={changeView}
            size="small"
          >
            <Tooltip title="Calendar View">
              <ToggleButton value="calendar" size="small">
                <CalendarMonthIcon />
              </ToggleButton>
            </Tooltip>
            <Tooltip title="Table View">
              <ToggleButton value="table" size="small">
                <ViewListIcon />
              </ToggleButton>
            </Tooltip>
          </ToggleButtonGroup>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        {view === "calendar" ? (
          <FullCalendarView events={events} />
        ) : (
          <SearchableDataGrid
            icon={<CalendarMonthIcon />}
            title={`Events`}
            columns={columns}
            rows={events}
            getRowId={(row) => row.event_id}
            getSelectedItemProperties={getSelectedItemProperties}
            initialPageSize={25}
            initialSortModel={[{ field: "start_datetime", sort: "asc" }]}
          />
        )}
      </AccordionDetails>
    </Accordion>
  );
}

export default CalendarAppSection;
