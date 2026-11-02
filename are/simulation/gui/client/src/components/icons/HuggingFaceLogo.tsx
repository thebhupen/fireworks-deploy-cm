// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import React from "react";
import HFLogo from "../assets/hf-logo-pirate.svg";

interface HuggingFaceIconProps {
  size?: number;
}

export default function HuggingFaceIcon({
  size = 21,
}: HuggingFaceIconProps): React.ReactElement {
  return (
    <img
      src={HFLogo}
      height={size}
      style={{
        filter: "grayscale(100%)",
      }}
    />
  );
}
