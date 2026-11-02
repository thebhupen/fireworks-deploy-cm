// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { ApartmentApp } from "./types";

export const ApartmentAppDetails = ({ app }: { app: ApartmentApp }) => {
  const apartments = app.apartments ?? {};
  const apartmentsCount = Object.keys(apartments).length;
  const savedApartments = app.saved_apartments ?? {};
  const savedApartmentsCount = Object.keys(savedApartments).length;

  return (
    <>
      <div>Total apartments: {apartmentsCount}</div>
      <div>Total saved apartments: {savedApartmentsCount}</div>
    </>
  );
};

export default ApartmentAppDetails;
