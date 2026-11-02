// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import MetaLogoSvg from "../assets/meta-logo.svg";

interface MetaLogoProps {
  size?: number | string;
}

const MetaLogo = ({ size = 36 }: MetaLogoProps) => {
  return <img src={MetaLogoSvg} alt="Meta Logo" width={size} height={size} />;
};

export default MetaLogo;
