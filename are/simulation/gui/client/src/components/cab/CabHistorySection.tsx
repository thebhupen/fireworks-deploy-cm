// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import HistoryIcon from "@mui/icons-material/History";
import { GridColDef } from "@mui/x-data-grid";
import * as React from "react";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import CollapsibleDataGrid from "../common/datagrid/CollapsibleDataGrid";
import { Ride } from "./types";

interface CabHistorySectionProps {
  title: string;
  data: Ride[];
}

/**
 * CabHistorySection component displays a history of cab rides with search functionality.
 *
 * @param {CabHistorySectionProps} props - Component properties.
 * @param {string} props.title - Title of the section.
 * @param {Ride[]} props.data - Array of ride data.
 * @returns {React.ReactNode} - Rendered component.
 */
function CabHistorySection({
  title,
  data,
}: CabHistorySectionProps): React.ReactNode {
  const columns: GridColDef[] = [
    { field: "ride_id", headerName: "Ride ID" },
    { field: "status", headerName: "Status" },
    { field: "service_type", headerName: "Service Type" },
    { field: "start_location", headerName: "Start Location" },
    { field: "end_location", headerName: "End Location" },
    {
      field: "price",
      headerName: "Price",
      renderCell: (params) => `${params.value.toFixed(2)}`,
      align: "right",
    },
    {
      field: "duration",
      headerName: "Duration",
      renderCell: (params) => `${params.value.toFixed(2)}`,
      align: "right",
    },
    {
      field: "time_stamp",
      headerName: "Time Stamp",
      renderCell: (params) =>
        params.row.time_stamp &&
        formatDateAndTimeFromTime(params.row.time_stamp * 1000),
    },
    {
      field: "distance_km",
      headerName: "Distance (km)",
      renderCell: (params) => `${params.value.toFixed(2)}`,
      align: "right",
    },
    { field: "delay", headerName: "Delay" },
  ];

  const getSelectedRideProperties = (ride: Ride) => {
    return {
      "Ride ID": ride?.ride_id,
      Status: ride?.status,
      "Service Type": ride?.service_type,
      "Start Location": ride?.start_location,
      "End Location": ride?.end_location,
      Price: ride?.price,
      Duration: ride?.duration,
      "Time Stamp": formatDateAndTimeFromTime((ride?.time_stamp ?? 0) * 1000),
      "Distance (km)": ride?.distance_km,
      Delay: ride?.delay,
      "Delay History":
        Array.isArray(ride?.delay_history) && ride.delay_history.length > 0
          ? ride.delay_history.join(", ")
          : "No delays",
    };
  };

  return (
    <CollapsibleDataGrid
      icon={<HistoryIcon />}
      title={title}
      columns={columns}
      rows={data}
      getRowId={(ride) => ride.ride_id}
      getSelectedItemProperties={getSelectedRideProperties}
      pageSizeOptions={[10, 25, 50, 100]}
      initialPageSize={10}
    />
  );
}

export default CabHistorySection;
