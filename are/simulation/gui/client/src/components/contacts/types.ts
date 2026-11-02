// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface Contact {
  id?: string;
  contact_id?: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  age: string;
  city_living: string;
  country: string;
  job: string;
  gender: string;
  nationality: string;
  status: string;
  description: string;
  address: string;
  is_user?: boolean;
}

export interface ContactsAppState {
  [id: string]: Contact;
}

export interface ContactsApp {
  app_name: AppName;
  contacts?: Record<string, Contact>;
}
