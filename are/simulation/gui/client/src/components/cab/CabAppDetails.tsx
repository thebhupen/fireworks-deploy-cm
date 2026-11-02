// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { CabApp } from "./types";

export const CabAppDetails = ({ app }: { app: CabApp }) => {
  const rideHistory = app.ride_history ?? [];
  const quotationHistory = app.quotation_history ?? [];
  return (
    <>
      <div>Ride History: {rideHistory.length}</div>
      <div>Quotation History: {quotationHistory.length}</div>
    </>
  );
};

export default CabAppDetails;
