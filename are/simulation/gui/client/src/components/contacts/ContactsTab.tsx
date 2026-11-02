// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import ContactsSection from "./ContactsAppSection";

function ContactsTab({ state }: { state: any }): React.ReactNode {
  const NO_CONTACTS_FOUND = "No contacts found.";

  if (!state || !state.contacts) {
    return <div>{NO_CONTACTS_FOUND}</div>;
  }

  const contacts = state.contacts;

  if (!contacts || Object.keys(contacts).length === 0) {
    return <div>{NO_CONTACTS_FOUND}</div>;
  }

  return <ContactsSection contacts={contacts} />;
}

export default ContactsTab;
