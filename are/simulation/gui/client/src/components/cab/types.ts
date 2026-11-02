// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface Ride {
  ride_id: string;
  status?: string | null;
  service_type: string | null;
  start_location: string | null;
  end_location: string | null;
  price?: number | null;
  duration: number | null;
  time_stamp: number | null;
  distance_km?: number | null;
  delay: number | null;
  delay_history: { [key: string]: any }[];
}

export interface RideServiceConfig {
  service_type?: string;
  nb_seats: number;
  price_per_km: number;
  base_delay_min: number;
  max_distance_km: number;
}

export interface CabApp {
  app_name: AppName;
  ride_history: Array<Ride>;
  quotation_history: Array<Ride>;
  app_id?: string;
  d_service_config: RideServiceConfig;
}
