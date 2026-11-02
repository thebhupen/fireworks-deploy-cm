// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import BrokenImageIcon from "@mui/icons-material/BrokenImage";
import { Tooltip } from "@mui/material";
import React, { useState } from "react";

interface ImageProps {
  src: string; // The source URL of the image
  alt?: string; // The alt text for the image
  style?: React.CSSProperties; // Optional styles to apply to the image
  iconStyle?: React.CSSProperties; // Optional styles to apply to the fallback icon
  width?: string | number; // Optional width of the image
  height?: string | number; // Optional height of the image
}

/**
 * Image component that displays an image and falls back to a BrokenImageIcon if the image fails to load.
 *
 * @param {ImageProps} props - The properties for the image component.
 * @param {string} props.src - The source URL of the image.
 * @param {string} [props.alt] - The alt text for the image.
 * @param {React.CSSProperties} [props.style] - Optional styles to apply to the image.
 * @param {string | number} [props.width] - Optional width of the image.
 * @param {string | number} [props.height] - Optional height of the image.
 */
const Image = ({ src, alt, style, width, height }: ImageProps) => {
  const [isError, setIsError] = useState(false);

  /**
   * Handles the error event when the image fails to load.
   */
  const handleError = () => {
    setIsError(true);
  };

  return isError ? (
    <Tooltip title={alt ?? `Image failed to load: ${src}`}>
      <BrokenImageIcon sx={{ ...style, width, height }} />
    </Tooltip>
  ) : (
    <img
      src={src}
      alt={alt}
      style={{ ...style, width, height }}
      onError={handleError}
    />
  );
};

export default Image;
