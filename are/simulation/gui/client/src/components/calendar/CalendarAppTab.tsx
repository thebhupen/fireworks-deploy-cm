// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import CalendarAppSection from "./CalendarAppSection";
import { CalendarEvent } from "./types";

function CalendarAppTab({ state }: { state: any }): React.ReactNode {
  const NO_EVENTS_FOUND = "No events found.";

  if (!state || !state.hasOwnProperty("events")) {
    return <div>{NO_EVENTS_FOUND}</div>;
  }

  const events = state["events"] as Record<string, CalendarEvent>;

  if (!events || Object.keys(events).length === 0) {
    return <div>{NO_EVENTS_FOUND}</div>;
  }

  return <CalendarAppSection data={events} />;
}

export default CalendarAppTab;
