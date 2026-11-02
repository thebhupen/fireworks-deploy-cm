// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface Item {
  price: number;
  available?: boolean;
  item_id?: string;
  options?: { [key: string]: any };
}

export interface Product {
  name: string;
  product_id?: string;
  variants?: { [key: string]: Item };
}

export interface CartItem {
  item_id: string;
  quantity: number;
  price: number;
  available?: boolean;
  options?: { [key: string]: any };
}

export interface Order {
  order_status: string;
  order_date: any;
  order_total: number;
  order_id?: string;
  order_items?: { [key: string]: CartItem };
}

export interface ShoppingApp {
  app_name?: AppName;
  products?: { [key: string]: Product };
  cart?: { [key: string]: CartItem };
  orders?: { [key: string]: Order };
  discount_codes?: { [key: string]: { [key: string]: number } };
}

export interface Variant extends Item {
  item_id: string;
}

export interface ProductView {
  product_id: string;
  name: string;
  variants: Variant[];
}

export interface OrderItem extends CartItem {
  item_id: string;
}

export interface OrderView {
  order_id?: string;
  order_status: string;
  order_date: number;
  order_total: number;
  order_items: OrderItem[];
}
