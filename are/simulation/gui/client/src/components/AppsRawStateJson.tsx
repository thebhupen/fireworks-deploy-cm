// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Card, CardContent } from "@mui/material";
import * as React from "react";
import JSONView from "./JSONView";

function AppsRawStateJson({ state }: { state: any }): React.ReactNode {
  return (
    <Card>
      <CardContent>
        <JSONView json={state} />
      </CardContent>
    </Card>
  );
}

export default AppsRawStateJson;
