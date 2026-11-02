// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { CityApp } from "./types";

export const CityAppDetails = ({ app }: { app: CityApp }) => {
  const crimeData = app.crime_data ?? {};
  const crimeDataCount = Object.keys(crimeData).length;

  return (
    <div>
      <div>Cities: {crimeDataCount}</div>
    </div>
  );
};

export default CityAppDetails;
