// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { CalendarApp } from "./types";

export const CalendarAppDetails = ({ app }: { app: CalendarApp }) => {
  const events = app.events ?? {};
  const eventsCount = Object.keys(events).length;

  return (
    <div>
      <div>Total Events: {eventsCount}</div>
    </div>
  );
};

export default CalendarAppDetails;
