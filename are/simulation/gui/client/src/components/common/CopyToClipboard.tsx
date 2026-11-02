// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { IconButton, Tooltip } from "@mui/material";
import useCopyToClipboard from "../../hooks/useCopyToClipboard";

/**
 * Component that provides a button to copy a given value to the clipboard.
 *
 * @param {string} value - The text value to be copied to the clipboard.
 * @param {string} [label="Copy to clipboard"] - The label for the tooltip when the button is not clicked.
 * @param {"small" | "medium" | "large"} [size="small"] - The size of the icon button.
 */
const CopyToClipboard = ({
  value,
  label = "Copy to clipboard",
  size = "small",
  color,
}: {
  value: string;
  label?: string;
  size?: "small" | "medium" | "large";
  color?: string;
}) => {
  const { isCopied, handleCopy } = useCopyToClipboard(value);

  return (
    <Tooltip title={isCopied ? "Copied!" : label}>
      <IconButton onClick={handleCopy} size={size}>
        <ContentCopyIcon fontSize="inherit" htmlColor={color} />
      </IconButton>
    </Tooltip>
  );
};

export default CopyToClipboard;
