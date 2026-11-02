// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  getNodesBounds,
  getViewportForBounds,
  useReactFlow,
} from "@xyflow/react";
import { toPng } from "html-to-image";
import { useCallback, useState } from "react";

function downloadImage(dataUrl: string) {
  const a = document.createElement("a");
  a.setAttribute("download", "are_simulation_events.png");
  a.setAttribute("href", dataUrl);
  a.click();
}

const VIEWPORT_CLASS_NAME = ".react-flow__viewport";
const IMAGE_WIDTH = 2400;
const IMAGE_HEIGHT = 1200;

const useDownloadDag = () => {
  const [isDownloading, setIsDownloading] = useState(false);
  const { getNodes } = useReactFlow();
  const downloadDag = useCallback(async () => {
    setIsDownloading(true);
    // we calculate a transform for the nodes so that all nodes are visible
    // we then overwrite the transform of the `.react-flow__viewport` element
    // with the style option of the html-to-image library
    const nodesBounds = getNodesBounds(getNodes());
    const viewport = getViewportForBounds(
      nodesBounds,
      IMAGE_WIDTH,
      IMAGE_HEIGHT,
      0.5,
      2,
      0.5,
    );
    const viewportElement = document.querySelector(
      VIEWPORT_CLASS_NAME,
    ) as HTMLElement;
    if (viewportElement === null) {
      console.error("Could not find react flow viewport element");
      return;
    }
    const backgroundColor = "#000";
    const url = await toPng(viewportElement, {
      backgroundColor: backgroundColor,
      width: IMAGE_WIDTH,
      height: IMAGE_HEIGHT,
      style: {
        width: `${IMAGE_WIDTH}`,
        height: `${IMAGE_HEIGHT}`,
        transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})`,
      },
    });
    downloadImage(url);
    setIsDownloading(false);
  }, [getNodes]);

  return { downloadDag, isDownloading };
};

export default useDownloadDag;
