// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ApartmentIcon from "@mui/icons-material/Apartment";
import { GridColDef } from "@mui/x-data-grid";
import * as React from "react";
import CollapsibleDataGrid from "../common/datagrid/CollapsibleDataGrid";
import { Apartment } from "./types";

const NUMBER_FORMAT = new Intl.NumberFormat();

function ApartmentsSection({
  title,
  data,
  icon,
}: {
  title: string;
  data: Apartment[];
  icon?: React.ReactNode;
}): React.ReactNode {
  const columns: GridColDef<Apartment>[] = [
    { field: "name", headerName: "Name", width: 200 },
    { field: "zip_code", headerName: "Zip Code", width: 75 },
    { field: "location", headerName: "Location", width: 250 },
    {
      field: "price",
      headerName: "Price",
      renderCell: (params) =>
        `${NUMBER_FORMAT.format(params.value.toFixed(2))}`,
      align: "right",
    },
    { field: "bedrooms", headerName: "Bedrooms" },
    { field: "bathrooms", headerName: "Bathrooms" },
    { field: "property_type", headerName: "Property Type" },
    { field: "square_footage", headerName: "Square Footage" },
    { field: "furnished_status", headerName: "Furnished Status", width: 150 },
    { field: "floor_level", headerName: "Floor Level" },
    { field: "pet_policy", headerName: "Pet Policy" },
    { field: "lease_term", headerName: "Lease Term" },
    {
      field: "amenities",
      headerName: "Amenities",
      renderCell: (params) => params.value.join(", "),
      width: 200,
    },
  ];

  const getSelectedItemProperties = (apartment: Apartment) => ({
    Name: apartment.name,
    "Zip Code": apartment.zip_code,
    Location: apartment.location,
    Price: `$${apartment.price}`,
    Bedrooms: apartment.bedrooms,
    Bathrooms: apartment.bathrooms,
    "Property Type": apartment.property_type,
    "Square Footage": `${apartment.square_footage} sqft`,
    "Furnished Status": apartment.furnished_status,
    "Floor Level": apartment.floor_level,
    "Pet Policy": apartment.pet_policy,
    "Lease Term": apartment.lease_term,
    Amenities: apartment.amenities.join(", "),
  });

  return (
    <CollapsibleDataGrid
      icon={icon ?? <ApartmentIcon />}
      title={title}
      columns={columns}
      rows={data}
      getRowId={(apartment) => apartment.apartment_id}
      getSelectedItemProperties={getSelectedItemProperties}
      pageSizeOptions={[10, 25, 50, 100]}
      initialPageSize={10}
    />
  );
}

export default ApartmentsSection;
