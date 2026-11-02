// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface CrimeDataPoint {
  id?: string;
  violent_crime: number;
  property_crime: number;
}

export interface CityApp {
  app_name?: AppName;
  api_call_count: number;
  api_call_limit: number;
  crime_data: { [key: string]: CrimeDataPoint };
  rate_limit_time?: number;
  rate_limit_exceeded: boolean;
}
