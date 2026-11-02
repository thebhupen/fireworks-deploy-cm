// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import TabsContextProvider from "../contexts/TabsContextProvider";
import { AppViews } from "../utils/types";
import LoadingStub from "./LoadingStub";

const ScenariosView = React.lazy(
  () => import("../views/scenarios/ScenariosView"),
);
const PlaygroundView = React.lazy(
  () => import("../views/playground/PlaygroundView"),
);
interface RouterProps {
  appView: string | null;
}

const renderViewFn = (appView: string | null) => {
  switch (appView) {
    case AppViews.SCENARIOS:
      return <ScenariosView />;
    case AppViews.PLAYGROUND: {
      const urlParams = new URLSearchParams(window.location.search);
      const groupId = urlParams.get("group_id");
      const initialTab = groupId != null ? "annotated-chat" : "agent-chat";
      return (
        <TabsContextProvider initialTab={initialTab}>
          <PlaygroundView />
        </TabsContextProvider>
      );
    }
    case AppViews.DISCONNECTED:
    default:
      return <LoadingStub />;
  }
};

function Router({ appView }: RouterProps): React.ReactNode {
  const renderView = () => renderViewFn(appView);

  return (
    <React.Suspense fallback={<LoadingStub />}>{renderView()}</React.Suspense>
  );
}

export default Router;
