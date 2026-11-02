// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { ShoppingApp } from "./types";

export const ShoppingAppDetails = ({ app }: { app: ShoppingApp }) => {
  const products = app.products ?? {};
  const productAvailable = Object.keys(products).length;
  const orders = app.orders ?? {};
  const orderCount = Object.keys(orders).length;
  const cart = app.cart ?? {};
  const cartCount = Object.keys(cart).length;

  return (
    <>
      <div>Products: {productAvailable}</div>
      <div>Cart: {cartCount}</div>
      <div>Orders: {orderCount}</div>
    </>
  );
};

export default ShoppingAppDetails;
