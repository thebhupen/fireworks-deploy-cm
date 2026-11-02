// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Contact, ContactsAppState } from "../components/contacts/types";
import { AppsState } from "./types";

export function getUserPersonaFromApps(appsState: AppsState): Contact | null {
  let userPersona = null;
  const ContactsApps = [...appsState].filter(
    (app) => app.app_name === "Contacts" || app.app_name === "ContactsApp",
  );
  if (ContactsApps.length > 0) {
    const contactsApp = ContactsApps[0] as ContactsAppState;
    const contacts = contactsApp.contacts;
    const contactsArray = Object.values(contacts ?? {});
    userPersona =
      contactsArray.find((contact: Contact) => contact.is_user) ?? null;
  }
  return userPersona;
}
