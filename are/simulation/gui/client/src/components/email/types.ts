// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface Email {
  sender: string;
  recipients: string[];
  subject: string;
  content: string;
  email_id: string;
  parent_id?: string;
  cc: string[];
  attachments?: Record<string, Uint8Array>;
  timestamp: number;
  is_read: boolean;
}

export interface ReturnedEmails {
  emails: Email[];
  emails_range: [number, number];
  total_returned_emails: number;
  total_emails: number;
}

export enum EmailFolderName {
  INBOX = "INBOX",
  SENT = "SENT",
  DRAFT = "DRAFT",
  TRASH = "TRASH",
}

export interface EmailFolder {
  folder_name: EmailFolderName;
  emails: Email[];
}

export interface EmailClientApp {
  app_name?: AppName;
  view_limit: number;
  folders: Record<EmailFolderName, EmailFolder>;
  user_email: string;
}
