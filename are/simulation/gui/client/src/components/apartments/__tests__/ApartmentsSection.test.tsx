// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

// ApartmentsSection.test.tsx
import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ApartmentsSection from "../ApartmentsSection";
import { Apartment } from "../types";

describe("ApartmentsSection", () => {
  it("renders without crashing", () => {
    const mockData: Apartment[] = [
      {
        apartment_id: "1",
        name: "Apartment 1",
        zip_code: "12345",
        location: "Location 1",
        price: 1000,
        bedrooms: 2,
        bathrooms: 1,
        property_type: "Condo",
        square_footage: 800,
        furnished_status: "Furnished",
        floor_level: "1",
        pet_policy: "Allowed",
        lease_term: "12 months",
        amenities: ["Pool", "Gym"],
      },
    ];

    const { container } = render(
      <ApartmentsSection title="Test Apartments" data={mockData} />,
    );
    expect(container).toBeDefined();
  });
});
