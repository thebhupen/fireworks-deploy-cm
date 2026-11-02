// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import LocalTaxiIcon from "@mui/icons-material/LocalTaxi";
import { GridColDef } from "@mui/x-data-grid";
import * as React from "react";
import { useMemo } from "react";
import CollapsibleDataGrid from "../common/datagrid/CollapsibleDataGrid";
import { RideServiceConfig } from "./types";

/**
 * CabServiceConfigSection component that displays a list of ride service configurations
 * and allows users to search and view details in a dialog.
 *
 * @param {Object} props - Component properties.
 * @param {string} props.title - Title of the section.
 * @param {RideServiceConfig[]} props.data - Array of ride service configurations.
 * @returns {React.ReactNode} - Rendered component.
 */
function CabServiceConfigSection({
  title,
  data,
}: {
  title: string;
  data: Record<string, RideServiceConfig>;
}): React.ReactNode {
  const rows = useMemo(
    () =>
      Object.entries(data).map(([serviceType, config]) => ({
        service_type: serviceType,
        ...config,
      })),
    [data],
  );

  const columns: GridColDef[] = [
    { field: "service_type", headerName: "Service Type", flex: 1 },
    { field: "nb_seats", headerName: "# of Seats", align: "right", flex: 1 },
    {
      field: "price_per_km",
      headerName: "Price per km",
      renderCell: (params) => `${params.value.toFixed(2)}`,
      align: "right",
      flex: 1,
    },
    {
      field: "base_delay_min",
      headerName: "Base Delay (Minutes)",
      align: "right",
      flex: 1,
    },
    {
      field: "max_distance_km",
      headerName: "Max Distance (km)",
      align: "right",
      flex: 1,
    },
  ];

  const getSelectedConfigProperties = (config: RideServiceConfig) => {
    return {
      "Service Type": config?.service_type,
      "# of Seats": config?.nb_seats,
      "Price per km": config?.price_per_km,
      "Base Delay (minutes)": config?.base_delay_min,
      "Max Distance (km)": config?.max_distance_km,
    };
  };

  return (
    <CollapsibleDataGrid
      icon={<LocalTaxiIcon />}
      title={title}
      columns={columns}
      rows={rows}
      getRowId={(config) => config.service_type!}
      getSelectedItemProperties={getSelectedConfigProperties}
      pageSizeOptions={[5, 10, 20]}
      initialPageSize={5}
    />
  );
}

export default CabServiceConfigSection;
