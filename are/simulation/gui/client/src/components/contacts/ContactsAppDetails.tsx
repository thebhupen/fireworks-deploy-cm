// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { ContactsApp } from "./types";

export const ContactsAppDetails = ({ app }: { app: ContactsApp }) => {
  const contacts = app.contacts ?? {};
  const contactsCount = Object.keys(contacts).length;

  return (
    <div>
      <div>Total Contacts: {contactsCount}</div>
    </div>
  );
};

export default ContactsAppDetails;
