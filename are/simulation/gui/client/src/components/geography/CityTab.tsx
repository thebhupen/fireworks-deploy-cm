// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { GridColDef } from "@mui/x-data-grid";
import * as React from "react";
import { useMemo } from "react";
import CollapsibleDataGrid from "../common/datagrid/CollapsibleDataGrid";
import { CityApp, CrimeDataPoint } from "./types";

interface CrimeDataPointView extends CrimeDataPoint {
  id: string;
}
function CityTab({ city }: { city: CityApp }): React.ReactNode {
  const crimeInfo = useMemo(() => city?.crime_data ?? {}, [city?.crime_data]);

  const cityList: CrimeDataPointView[] = useMemo(() => {
    return Object.entries(crimeInfo || {}).map(([id, city]) => ({
      id,
      violent_crime: city.violent_crime,
      property_crime: city.property_crime,
    }));
  }, [crimeInfo]);

  const columns: GridColDef[] = [
    { field: "id", headerName: "Zip Code", width: 150 },
    { field: "violent_crime", headerName: "Violent Crime", width: 150 },
    { field: "property_crime", headerName: "Property Crime", width: 150 },
  ];

  const getSelectedItemProperties = (item: CrimeDataPointView) => ({
    "Zip Code": item.id,
    "Violent Crime": item.violent_crime || "",
    "Property Crime": item.property_crime || "",
  });

  const getRowId = (row: CrimeDataPointView) => row.id;

  const NO_DATA_FOUND = "No data found.";

  if (!city || !city.crime_data) {
    return <div>{NO_DATA_FOUND}</div>;
  }

  const crimeData = city.crime_data;

  if (!crimeData || Object.keys(crimeData).length === 0) {
    return <div>{NO_DATA_FOUND}</div>;
  }

  return (
    <CollapsibleDataGrid
      title="City Crime Data"
      columns={columns}
      rows={cityList}
      getSelectedItemProperties={getSelectedItemProperties}
      getRowId={getRowId}
      initialPageSize={25}
    />
  );
}

export default CityTab;
