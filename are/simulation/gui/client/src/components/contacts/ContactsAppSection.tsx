// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ContactsIcon from "@mui/icons-material/Contacts";
import { Typography } from "@mui/material";
import * as React from "react";
import { useMemo } from "react";
import CollapsibleDataGrid from "../common/datagrid/CollapsibleDataGrid";
import { Contact } from "./types";

function ContactsSection({
  contacts,
}: {
  contacts: Record<string, Contact>;
}): React.ReactNode {
  const contactsList = useMemo(() => {
    return Object.entries(contacts || {}).map(([id, contact]) => ({
      id,
      ...contact,
      first_name: contact.first_name || "Unknown",
    }));
  }, [contacts]);

  const columns = [
    { field: "first_name", headerName: "First Name", width: 125 },
    { field: "last_name", headerName: "Last Name", width: 125 },
    { field: "email", headerName: "Email", width: 150 },
    { field: "phone", headerName: "Phone", width: 150 },
    { field: "age", headerName: "Age", width: 30 },
    { field: "city_living", headerName: "City", width: 150 },
    { field: "country", headerName: "Country", width: 150 },
    { field: "job", headerName: "Job", width: 200 },
  ];

  const getSelectedItemProperties = (contact: Contact) => ({
    Name: `${contact.first_name} ${contact.last_name}`,
    Email: contact.email,
    Phone: contact.phone,
    Age: contact.age,
    City: contact.city_living,
    Country: contact.country,
    Job: contact.job,
    Gender: contact.gender,
    Nationality: contact.nationality,
    Status: contact.status,
    Description: <Typography maxWidth={400}>{contact.description}</Typography>,
    Address: contact.address,
  });

  const getRowId = (contact: Contact) => contact.id!;

  return (
    <CollapsibleDataGrid
      icon={<ContactsIcon />}
      title={`Contacts`}
      columns={columns}
      rows={contactsList}
      getSelectedItemProperties={getSelectedItemProperties}
      getRowId={getRowId}
      initialPageSize={25}
    />
  );
}

export default ContactsSection;
