// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { useState } from "react";

const useCopyToClipboard = (value: string) => {
  const [isCopied, setIsCopied] = useState(false);

  /**
   * Handles the copy action by writing the value to the clipboard and updating the copied state.
   */
  const handleCopy = (e?: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    e?.stopPropagation();
    navigator.clipboard.writeText(value);
    setIsCopied(true);
    setTimeout(() => {
      setIsCopied(false);
    }, 2000);
  };

  return { isCopied, handleCopy };
};

export default useCopyToClipboard;
