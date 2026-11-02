// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import BugReportIcon from "@mui/icons-material/BugReport";
import { GITHUB_REPO_URL } from "../../../utils/const";
import SidebarButton from "./SidebarButton";

interface ReportBugButtonProps {
  showLabel?: boolean;
}

export default function ReportBugButton({
  showLabel = false,
}: ReportBugButtonProps) {
  return (
    <SidebarButton
      startIcon={<BugReportIcon fontSize="small" />}
      label="Report bug"
      isExpanded={showLabel}
      onClick={() => {
        window.open(`${GITHUB_REPO_URL}/issues/new`, "_blank");
      }}
    />
  );
}
