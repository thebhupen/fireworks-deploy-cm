// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SellIcon from "@mui/icons-material/Sell";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import StoreIcon from "@mui/icons-material/Store";
import ViewListIcon from "@mui/icons-material/ViewList";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Card,
  CardContent,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";
import * as React from "react";
import { useCallback, useMemo } from "react";
import { formatDateFromTime } from "../../utils/TimeUtils";
import CollapsibleDataGrid from "../common/datagrid/CollapsibleDataGrid";
import {
  CartItem,
  Order,
  OrderView,
  Product,
  ProductView,
  Variant,
} from "./types";

interface ShoppingAppSectionProps {
  products: { [key: string]: Product };
  cart?: { [key: string]: CartItem };
  orders?: { [key: string]: Order };
  discountCodes?: { [key: string]: { [key: string]: number } };
}

function ShoppingAppSection({
  products,
  cart,
  orders,
  discountCodes,
}: ShoppingAppSectionProps): React.ReactNode {
  // Convert products into a list of products and variants
  const productList: ProductView[] = useMemo(() => {
    return Object.entries(products || {}).map(([id, product]) => ({
      product_id: id,
      name: product.name || "Unknown Product",
      variants: Object.entries(product.variants || {}).map(
        ([variantId, variant]): Variant => ({
          ...variant,
          item_id: variantId,
          price: variant.price || 0,
        }),
      ),
    }));
  }, [products]);

  // variant id to product name mapping
  const itemIdToProductName: Record<string, string> = useMemo(() => {
    const map: Record<string, string> = {};
    // Iterate through each product
    productList.forEach((product) => {
      const productName = product.name;

      // Iterate through each variant of the product
      product.variants.forEach((variant) => {
        const itemId = variant.item_id;
        map[itemId] = productName; // Map item_id to product name
      });
    });
    return map;
  }, [productList]);

  const productColumns: GridColDef[] = [
    { field: "name", headerName: "Product Name", width: 500 },
    {
      field: "variants",
      headerName: "Number of Variants",
      width: 150,
      renderCell: (params) => params.row.variants.length,
      align: "right",
    },
  ];

  const searchProducts = (
    products: ProductView[],
    searchTerm: string,
  ): ProductView[] => {
    if (!searchTerm) {
      return products;
    }

    return products.filter((product) => {
      const nameMatches = product.name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const idMatches = product.product_id
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const variantMatches = product.variants.some((variant) => {
        const idMatch = variant.item_id
          .toLowerCase()
          .includes(searchTerm.toLowerCase());
        const optionsMatch = Object.values(variant.options || {}).some(
          (optionValue) =>
            optionValue
              .toString()
              .toLowerCase()
              .includes(searchTerm.toLowerCase()),
        );
        const priceMatch = variant.price.toString().includes(searchTerm);
        const availabilityMatch = variant.available
          ?.toString()
          .toLowerCase()
          .includes(searchTerm.toLowerCase());

        return idMatch || optionsMatch || priceMatch || availabilityMatch;
      });

      return nameMatches || idMatches || variantMatches;
    });
  };

  const getSelectedProductTitle = (product: ProductView) => {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <SellIcon />
        <span>{product.name}</span>
      </Stack>
    );
  };

  const getSelectedProductContent = (product: ProductView) => {
    const options = Object.keys(product.variants[0]?.options ?? {}) ?? [];
    return (
      <Stack spacing={1}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Variant ID</TableCell>
                {options.map((option) => (
                  <TableCell key={option}>
                    {option.replace(/_/g, " ")}
                  </TableCell>
                ))}
                <TableCell>Price</TableCell>
                <TableCell>Available</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {product.variants.map((variant) => (
                <TableRow key={variant.item_id}>
                  <TableCell>{variant.item_id}</TableCell>
                  {options.map((option) => (
                    <TableCell key={`${variant.item_id}-${option}`}>
                      {variant.options?.[option] ?? ""}
                    </TableCell>
                  ))}
                  <TableCell>{variant.price.toFixed(2)}</TableCell>
                  <TableCell>{variant.available ? "Yes" : "No"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Typography>Product ID: {product.product_id}</Typography>
      </Stack>
    );
  };

  // Cart section
  const cartItems: CartItem[] = Object.entries(cart || {}).map(
    ([itemId, { quantity, ...item }]) => ({
      ...item,
      item_id: itemId,
      quantity,
    }),
  );

  const totalCartQuantity = cartItems.reduce(
    (sum, item) => sum + item.quantity,
    0,
  );

  // Orders section
  const orderList: OrderView[] = Object.values(orders || {}).map((order) => ({
    ...order,
    order_items: Object.entries(order.order_items ?? {}).map(
      ([itemId, item]) => ({
        ...item,
        item_id: itemId,
      }),
    ),
  }));

  const orderColumns: GridColDef[] = [
    { field: "order_id", headerName: "Order ID", width: 150 },
    { field: "order_status", headerName: "Status", width: 150 },
    {
      field: "order_date",
      headerName: "Date",
      width: 150,
      renderCell: (params) => formatDateFromTime(params.value),
    },
    {
      field: "order_total",
      headerName: "Total",
      width: 150,
      renderCell: (params) => `$${params.value.toFixed(2)}`,
    },
    {
      field: "order_items",
      headerName: "Items",
      width: 150,
      renderCell: (params) => params.value.length,
    },
  ];

  const getSelectedOrderProperties = (order: OrderView) => {
    return {
      "Order ID": order.order_id,
      Status: order.order_status,
      Date: formatDateFromTime(order.order_date),
      Total: `$${order.order_total.toFixed(2)}`,
      "Total Items": order.order_items.reduce(
        (sum, item) => sum + item.quantity,
        0,
      ),
    };
  };

  const getSelectedOrderContent = useCallback(
    (order: OrderView) => {
      return (
        <Card>
          <CardContent>
            {order.order_items.map((item) => (
              <div key={item.item_id}>
                {itemIdToProductName[item.item_id]} - Quantity: {item.quantity}{" "}
                - Price: ${item.price.toFixed(2)}
                <br />
                <b>Total for this item:</b> $
                {(item.price * item.quantity).toFixed(2)}
              </div>
            ))}
          </CardContent>
        </Card>
      );
    },
    [itemIdToProductName],
  );

  // Extracting discount codes from the provided structure
  const discountCodeList = Object.entries(discountCodes || {}).flatMap(
    ([productId, codes]) =>
      Object.entries(codes).map(([code, value]) => ({
        code,
        value,
        productId,
      })),
  );

  const discountCodeColumns: GridColDef[] = [
    { field: "productName", headerName: "Product Name", width: 200 },
    { field: "productId", headerName: "Variant Id", width: 150 },
    { field: "code", headerName: "Discount Code", width: 150 },
    {
      field: "value",
      headerName: "Discount Value (%)",
      width: 150,
      renderCell: (params) => `${params.value}%`,
    },
  ];

  // Prepare rows for the discount codes data grid
  const discountCodeRows = discountCodeList.map((discount, index) => ({
    id: index, // Unique identifier for each row
    productName: itemIdToProductName[discount.productId] || "Unknown Product",
    productId: discount.productId,
    code: discount.code,
    value: discount.value,
  }));

  return (
    <>
      <CollapsibleDataGrid
        icon={<StoreIcon />}
        title="Products"
        columns={productColumns}
        rows={productList}
        getRowId={(row) => row.product_id}
        getSelectedItemTitle={getSelectedProductTitle}
        getSelectedItemContent={getSelectedProductContent}
        searchFn={searchProducts}
      />
      <Accordion disableGutters defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Stack direction="row" alignItems={"center"} spacing={1}>
            <ShoppingCartIcon />
            <span>{`Cart (${totalCartQuantity})`}</span>
          </Stack>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Item ID</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Quantity</TableCell>
                  <TableCell>Price</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {cartItems.map((item) => (
                  <TableRow key={item.item_id}>
                    <TableCell>{item.item_id}</TableCell>
                    <TableCell>{itemIdToProductName[item.item_id]}</TableCell>
                    <TableCell>{item.quantity}</TableCell>
                    <TableCell align="right">{item.price.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
                <TableRow>
                  <TableCell colSpan={3}>Total</TableCell>
                  <TableCell align="right">
                    {cartItems
                      .reduce(
                        (sum, item) => sum + item.price * item.quantity,
                        0,
                      )
                      .toFixed(2)}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>
      <CollapsibleDataGrid
        icon={<ViewListIcon />}
        title="Orders"
        columns={orderColumns}
        rows={orderList}
        getRowId={(row) => row.order_id ?? ""}
        getSelectedItemProperties={getSelectedOrderProperties}
        getSelectedItemContent={getSelectedOrderContent}
      />
      <CollapsibleDataGrid
        icon={<SellIcon />}
        title={`Discount Codes`}
        columns={discountCodeColumns}
        rows={discountCodeRows}
        getRowId={(row) => row.id.toString()}
      />
    </>
  );
}

export default ShoppingAppSection;
