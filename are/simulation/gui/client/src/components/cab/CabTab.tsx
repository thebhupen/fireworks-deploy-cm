// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import CabHistorySection from "./CabHistorySection";
import CabServiceConfigSection from "./CabServiceConfigSection";

interface CabTabProps {
  state: any;
}

function CabTab({ state }: CabTabProps): React.ReactNode {
  const NO_CAB_FOUND = "No cab information found.";

  if (
    !state ||
    !state.hasOwnProperty("ride_history") ||
    !state.hasOwnProperty("quotation_history") ||
    !state.hasOwnProperty("d_service_config")
  ) {
    return <div>{NO_CAB_FOUND}</div>;
  }

  const rideHistory = state["ride_history"];
  const quotationHistory = state["quotation_history"];
  const dServiceConfig = state["d_service_config"];

  return (
    <>
      <CabHistorySection
        title="Ride History"
        data={rideHistory}
        key="ride_history"
      />
      <CabHistorySection
        title="Quotation History"
        data={quotationHistory}
        key="quotation_history"
      />
      <CabServiceConfigSection
        title="Service Config"
        data={dServiceConfig}
        key="d_service_config"
      />
    </>
  );
}

export default CabTab;
