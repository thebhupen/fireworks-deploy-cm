// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { EventClickArg, EventInput } from "@fullcalendar/core/index.js";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import SearchIcon from "@mui/icons-material/Search";
import {
  alpha,
  Box,
  FormControl,
  Stack,
  styled,
  TextField,
} from "@mui/material";
import { useContext, useMemo, useState } from "react";
import ScenarioContext from "../../contexts/ScenarioContext";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import DetailsDialog from "../common/DetailsDialog";
import { CalendarEvent } from "./types";

/**
 * Applies MUI theme to the calendar inside this component
 */
const StyledCalendarBox = styled(Box)(({ theme }) => ({
  "--fc-page-bg-color": theme.palette.background.paper,
  "--fc-neutral-text-color": theme.palette.text.secondary,
  "--fc-border-color": theme.palette.divider,
  "--fc-button-text-color": theme.palette.primary.contrastText,
  "--fc-button-bg-color": theme.palette.primary.main,
  "--fc-button-border-color": theme.palette.primary.main,
  "--fc-button-hover-bg-color": theme.palette.primary.dark,
  "--fc-button-hover-border-color": theme.palette.primary.dark,
  "--fc-button-active-bg-color": theme.palette.primary.dark,
  "--fc-button-active-border-color": theme.palette.primary.dark,
  "--fc-event-bg-color": theme.palette.primary.main,
  "--fc-event-border-color": theme.palette.info.main,
  "--fc-event-text-color": theme.palette.common.white,
  "--fc-bg-event-color": theme.palette.secondary.main,
  "--fc-highlight-color": alpha(theme.palette.secondary.main, 0.5),
  "--fc-today-bg-color": alpha(theme.palette.primary.main, 0.15),
  "--fc-now-indicator-color": theme.palette.error.main,
  ".fc-button": {
    "border-radius": theme.shape.borderRadius,
  },
  "thead th": {
    "border-top-right-radius": theme.shape.borderRadius,
    "border-top-left-radius": theme.shape.borderRadius,
  },
  table: {
    "border-radius": theme.shape.borderRadius,
  },
  a: {
    color: "inherit",
  },
}));

/**
 * FullCalendarView component that displays a calendar with events and a search functionality.
 *
 * @param {Object} props - Component properties.
 * @param {CalendarEvent[]} props.events - Array of calendar events to be displayed.
 */
function FullCalendarView({ events }: { events: CalendarEvent[] }) {
  const [selectedEvent, setSelectedEvent] = useState<EventInput | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const startTime = useContext(ScenarioContext).startTime;

  /**
   * Handles the event click by setting the selected event.
   *
   * @param {EventClickArg} info - Information about the clicked event.
   */
  const handleEventClick = (info: EventClickArg) => {
    setSelectedEvent(info.event as EventInput);
  };

  const handleClose = () => {
    setSelectedEvent(null);
  };

  const calendarEvents: EventInput[] = useMemo(() => {
    return events
      .filter((event) =>
        Object.values(event).some((value) =>
          (value ?? "")
            .toString()
            .toLowerCase()
            .includes(searchTerm.toLowerCase()),
        ),
      )
      .map((event) => ({
        id: event.event_id,
        title: event.title,
        start: event.start_datetime * 1000, // Using the original UNIX timestamp
        end: event.end_datetime * 1000, // Using the original UNIX timestamp
        extendedProps: {
          tag: event.tag,
          description: event.description,
          location: event.location,
          attendees: event.attendees,
        },
      }));
  }, [events, searchTerm]);

  const startDay: EventInput = {
    id: "-1",
    title: "Start",
    start: startTime * 1000,
    end: (startTime + 1) * 1000,
    allDay: false,
    color: "#4f4",
    textColor: "#333",
    display: "block",
    extendedProps: {
      tag: "System",
      description: "Scenario start time",
      location: "Paris",
    },
  };

  return (
    <Stack spacing={1}>
      <FormControl fullWidth>
        <TextField
          placeholder={`Search Events...`}
          onChange={(e) => setSearchTerm(e.target.value)}
          slotProps={{
            input: {
              startAdornment: <SearchIcon />,
            },
          }}
          size="small"
        />
      </FormControl>
      <StyledCalendarBox>
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay",
          }}
          events={[startDay, ...calendarEvents]}
          eventClick={handleEventClick}
          now={startTime * 1000}
          height="auto"
          timeZone="UTC" // Update timeZone to UTC to make it consistent with other time
          initialDate={startTime * 1000}
          firstDay={1}
        />
      </StyledCalendarBox>
      <DetailsDialog
        isOpen={!!selectedEvent}
        onClose={handleClose}
        title={selectedEvent?.title ?? "Event"}
        icon={<CalendarMonthIcon />}
        properties={{
          ID: selectedEvent?.id,
          Title: selectedEvent?.title,
          Description: selectedEvent?.extendedProps?.description,
          "Start Time": formatDateAndTimeFromTime(
            selectedEvent?.start as number,
          ),
          "End Time": formatDateAndTimeFromTime(selectedEvent?.end as number),
          Tag: selectedEvent?.extendedProps?.tag,
          Location: selectedEvent?.extendedProps?.location,
          Attendees: selectedEvent?.extendedProps?.attendees?.join(", "),
        }}
      />
    </Stack>
  );
}

export default FullCalendarView;
