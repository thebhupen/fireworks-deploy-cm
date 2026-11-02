// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import InboxIcon from "@mui/icons-material/Inbox";
import { Card, CardContent, Typography } from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import * as React from "react";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import CollapsibleDataGrid from "../common/datagrid/CollapsibleDataGrid";
import { Email } from "./types";

/**
 * EmailFolderSection component displays a collapsible data grid of emails within a folder.
 *
 * @param {object} props - The properties for the component.
 * @param {string} props.title - The title of the email folder.
 * @param {{ emails: Email[] }} props.data - The data containing emails to display.
 * @returns {React.ReactNode} The rendered component.
 */
function EmailFolderSection({
  title,
  data,
}: {
  title: string;
  data: { emails: Email[] };
}): React.ReactNode {
  const columns: GridColDef[] = [
    { field: "sender", headerName: "Sender", width: 200 },
    {
      field: "recipients",
      headerName: "Recipients",
      renderCell: (params) => params.value.join(", "),
      width: 200,
    },
    { field: "subject", headerName: "Subject", width: 200 },
    { field: "content", headerName: "Message", width: 400 },
    {
      field: "timestamp",
      headerName: "Date",
      renderCell: (params) => formatDateAndTimeFromTime(params.value * 1000),
      width: 200,
    },
    {
      field: "attachments",
      headerName: "Attachments",
      renderCell: (params) =>
        params.value ? Object.keys(params.value).length : 0,
      width: 100,
    },
  ];

  const getSelectedItemProperties = (email: Email) => ({
    From: email.sender,
    To: email.recipients.join(", "),
    CC: email.cc.join(", "),
    Subject: email.subject,
    Date: formatDateAndTimeFromTime(email.timestamp * 1000),
    Attachments: email.attachments ? Object.keys(email.attachments).length : 0,
    ID: email.email_id,
  });

  const getSelectedItemContent = (email: Email) => {
    return (
      <Card>
        <CardContent>
          <Typography>{email.content}</Typography>
        </CardContent>
      </Card>
    );
  };

  const getRowId = (email: Email) => email.email_id;

  return (
    <CollapsibleDataGrid
      icon={<InboxIcon />}
      title={title}
      columns={columns}
      rows={data.emails}
      getSelectedItemTitle={(email: Email) => email.subject}
      getSelectedItemProperties={getSelectedItemProperties}
      getSelectedItemContent={getSelectedItemContent}
      getRowId={getRowId}
    />
  );
}

export default EmailFolderSection;
