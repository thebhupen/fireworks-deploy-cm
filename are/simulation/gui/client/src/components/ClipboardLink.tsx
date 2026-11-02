// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import LinkIcon from "@mui/icons-material/Link";
import { IconButton, Tooltip } from "@mui/material";
import { useState } from "react";

export function ClipboardLink({
  content,
  tooltip,
}: {
  content?: string;
  tooltip?: string;
}) {
  const [success, setSuccess] = useState(false);
  return (
    <Tooltip title={success ? "Copied!" : (tooltip ?? "Copy to clipboard")}>
      <span>
        <IconButton
          disabled={content == null}
          size="medium"
          onClick={() => {
            if (content == null) {
              return;
            }

            navigator.clipboard.writeText(content);
            setSuccess(true);
            setTimeout(() => setSuccess(false), 1000);
          }}
        >
          <LinkIcon />
        </IconButton>
      </span>
    </Tooltip>
  );
}
