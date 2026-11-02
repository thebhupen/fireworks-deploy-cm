// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { EmailClientApp, EmailFolder } from "./types";

export const EmailClientAppDetails = ({ app }: { app: EmailClientApp }) => {
  return Object.entries(app.folders ?? {}).map(
    ([folderName, folderData], index) => {
      const emailFolder = folderData as EmailFolder;
      const unreadCount = emailFolder.emails.filter(
        (email) => !email.is_read,
      ).length;
      return (
        <div key={`${folderName}-${index}`}>
          {folderName} ({emailFolder.emails.length}){" "}
          {unreadCount > 0 && `[${unreadCount} new]`}
        </div>
      );
    },
  );
};

export default EmailClientAppDetails;
