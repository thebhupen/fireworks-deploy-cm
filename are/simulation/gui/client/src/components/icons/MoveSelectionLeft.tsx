// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

const MoveSelectionLeft = ({ width = 21, height = 21 }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={width}
    height={height}
    viewBox="0 0 16 16"
    fill="none"
  >
    <g opacity="0.5">
      <mask
        id="mask0_2089_196806"
        style={{ maskType: "alpha" }}
        maskUnits="userSpaceOnUse"
        x="0"
        y="0"
        width="16"
        height="16"
      >
        <rect
          width="16"
          height="16"
          fill="#D9D9D9"
          style={{
            fill: "#D9D9D9",
            fillOpacity: 1,
          }}
        />
      </mask>
      <g mask="url(#mask0_2089_196806)">
        <path
          d="M1.33301 12V4H9.33301V12H1.33301ZM10.6663 5.33333V4H11.9997V5.33333H10.6663ZM10.6663 12V10.6667H11.9997V12H10.6663ZM13.333 5.33333V4H14.6663V5.33333H13.333ZM13.333 8.66667V7.33333H14.6663V8.66667H13.333ZM13.333 12V10.6667H14.6663V12H13.333Z"
          fill="white"
          fillOpacity="0.87"
          style={{
            fill: "white",
            fillOpacity: 0.87,
          }}
        />
      </g>
    </g>
  </svg>
);

export default MoveSelectionLeft;
