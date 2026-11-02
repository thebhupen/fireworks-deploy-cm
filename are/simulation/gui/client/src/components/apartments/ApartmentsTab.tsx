// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import FavoriteIcon from "@mui/icons-material/Favorite";
import * as React from "react";
import { useMemo } from "react";
import ApartmentsSection from "./ApartmentsSection";
import { Apartment } from "./types";

function ApartmentsTab({ state }: { state: any }): React.ReactNode {
  const NO_APARTMENTS_FOUND = "No apartments found.";

  const apartments: Apartment[] = useMemo(
    () => Object.values(state["apartments"]),
    [state["apartments"]],
  );
  const savedApartmentKeys: string[] = state["saved_apartments"];
  const savedApartments: Apartment[] = useMemo(() => {
    return apartments.filter((apartment) =>
      savedApartmentKeys.includes(apartment.apartment_id),
    );
  }, [apartments, savedApartmentKeys]);

  if (!state || !state.hasOwnProperty("apartments")) {
    return <div>{NO_APARTMENTS_FOUND}</div>;
  }

  return (
    <>
      <ApartmentsSection title="Apartment" data={apartments} key="apartments" />
      <ApartmentsSection
        title="Saved Apartments"
        data={savedApartments}
        key="saved_apartments"
        icon={<FavoriteIcon />}
      />
    </>
  );
}

export default ApartmentsTab;
