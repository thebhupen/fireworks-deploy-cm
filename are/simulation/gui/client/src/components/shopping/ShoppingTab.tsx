// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import ShoppingAppSection from "./ShoppingAppSection";
import { ShoppingApp } from "./types";

/**
 * ShoppingTab component displays the shopping section of the application.
 * It checks for the presence of products in the state and renders the ShoppingAppSection
 * with the available products, cart, orders, and discount codes.
 *
 * @param {Object} props - The component props.
 * @param {ShoppingApp} props.state - The state containing products, cart, orders, and discount codes.
 * @returns {React.ReactNode} The rendered component.
 */
function ShoppingTab({ state }: { state: ShoppingApp }): React.ReactNode {
  const NO_PRODUCTS_FOUND = "No products found.";

  // Ensure state exists and has 'products'
  if (!state || !state.products) {
    return <div>{NO_PRODUCTS_FOUND}</div>;
  }

  const { products, cart, orders, discount_codes: discountCodes } = state;

  // Check if products exist and if the object has any items
  if (!products || Object.keys(products).length === 0) {
    return <div>{NO_PRODUCTS_FOUND}</div>;
  }

  // Pass the products to the ShoppingAppSection
  return (
    <ShoppingAppSection
      products={products}
      cart={cart}
      orders={orders}
      discountCodes={discountCodes}
    />
  );
}

export default ShoppingTab;
