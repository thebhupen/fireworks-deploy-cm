// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import EmailFolderSection from "./EmailFolderSection";
import { EmailClientApp } from "./types";

const NO_FOLDERS_MESSAGE = "No folders found.";

/**
 * EmailTab component renders the email folders for a given email client state.
 *
 * @param {Object} props - The component props.
 * @param {EmailClientApp} props.state - The state of the email client app.
 * @returns {React.ReactNode} The rendered component.
 */
function EmailTab({ state }: { state: EmailClientApp }): React.ReactNode {
  if (!state || !state.folders || Object.keys(state.folders).length === 0) {
    return <div>{NO_FOLDERS_MESSAGE}</div>;
  }

  const folderSections = Object.entries(state.folders).map(
    ([folderName, folderData]) => (
      <EmailFolderSection
        title={folderName}
        data={folderData}
        key={folderName}
      />
    ),
  );

  return <>{folderSections}</>;
}

export default EmailTab;
