// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface CalendarEvent {
  event_id: string;
  title: string;
  description: string;
  start_datetime: number;
  end_datetime: number;
  tag: string;
  location: string;
  attendees: string[];
}

export interface CalendarApp {
  app_name: AppName;
  events?: Record<string, CalendarEvent>;
}
