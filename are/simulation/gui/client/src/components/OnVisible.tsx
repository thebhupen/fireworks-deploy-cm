// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { useEffect, useRef } from "react";

export default function OnVisible({
  onVisible,
  rootMargin = "0px",
}: {
  onVisible: () => void;
  rootMargin?: string;
}): React.ReactNode {
  const divRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const current = divRef.current;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          onVisible();
        }
      },
      {
        root: null, // Uses the viewport by default
        threshold: 0.1, // Trigger when 10% of the div is visible
        rootMargin: rootMargin, // Allow customizing the root margin
      },
    );

    if (current) {
      observer.observe(current);
    }

    return () => {
      if (current) {
        observer.unobserve(current);
      }
    };
  }, [onVisible, rootMargin]);

  return (
    <div
      ref={divRef}
      style={{
        position: "relative",
        display: "block",
        minHeight: "20px",
        height: "20px",
        width: "100%",
        opacity: 0,
        flexShrink: 0,
      }}
    />
  );
}
