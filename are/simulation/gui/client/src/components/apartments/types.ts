// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface Apartment {
  name: string;
  zip_code: string;
  location: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  property_type: string;
  square_footage: number;
  furnished_status: string;
  floor_level: string;
  pet_policy: string;
  lease_term: string;
  amenities: string[];
  apartment_id: string;
}

export interface ApartmentsAppState {
  [id: string]: Apartment;
}

export interface ApartmentApp {
  app_name: AppName;
  apartments?: Record<string, Apartment>;
  saved_apartments?: Record<string, Apartment>;
}
