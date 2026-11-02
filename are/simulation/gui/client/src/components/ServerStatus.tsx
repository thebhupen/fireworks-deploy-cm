// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import type { ServerStatusQuery } from "./__generated__/ServerStatusQuery.graphql";

import { Box, Stack, Tooltip } from "@mui/material";
import * as React from "react";
import { useContext, useEffect, useState } from "react";
import { fetchQuery, graphql } from "relay-runtime";
import { useNotifications } from "../contexts/NotificationsContextProvider";
import SessionIdContext from "../contexts/SessionIdContext";
import { useWebSocket } from "../contexts/WebSocketProvider";
import useRelayEnvironment from "../relay/RelayEnvironment";
import { BASE_URL } from "../utils/const";
import { formatLocalDateFromTime } from "../utils/TimeUtils";
import CopyToClipboard from "./common/CopyToClipboard";
import { AgentIcon } from "./icons/AgentIcon";

export function ServerStatus(): React.ReactNode {
  const sessionId = useContext<string>(SessionIdContext);
  const environment = useRelayEnvironment();
  const { notify } = useNotifications();

  const { status: connectionStatus, statusChangedTime } = useWebSocket();
  const date = formatLocalDateFromTime(statusChangedTime);
  const [serverId, setServerId] = useState<string>("");
  const [serverVersion, setServerVersion] = useState<string>("");

  const ServerStatusBarQuery = graphql`
    query ServerStatusQuery {
      serverInfo {
        serverId
        serverVersion
      }
    }
  `;

  useEffect(() => {
    const subscription = fetchQuery<ServerStatusQuery>(
      environment,
      ServerStatusBarQuery,
      {},
    ).subscribe({
      next: (data) => {
        setServerId(data.serverInfo.serverId);
        setServerVersion(data.serverInfo.serverVersion);
      },
      error: (err: Error) => {
        console.error(err);
        notify({ message: "Error: " + JSON.stringify(err), type: "error" });
      },
    });
    return () => subscription.unsubscribe();
  }, [
    connectionStatus,
    statusChangedTime,
    ServerStatusBarQuery,
    environment,
    notify,
  ]);

  const tooltipContent = (
    <>
      <Stack direction={"row"} alignItems="center" spacing={1}>
        <span>Session ID: {sessionId}</span>
        <CopyToClipboard value={sessionId} label="Copy Session ID" />
      </Stack>
      <div style={{ display: "flex", alignItems: "center" }}>
        <span>Server: </span>
        {BASE_URL ? (
          <a
            href={BASE_URL}
            target="_blank"
            rel="noopener noreferrer"
            style={{ marginLeft: "5px", color: "white" }}
          >
            {BASE_URL}
          </a>
        ) : (
          <span style={{ marginLeft: "5px" }}>{serverId}</span>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center" }}>
        Version: {serverVersion}
      </div>
      <div style={{ display: "flex", alignItems: "center" }}>
        {connectionStatus} at {date}
      </div>
    </>
  );

  return (
    <Tooltip title={tooltipContent}>
      <span data-testid="server-status">
        <AgentIcon>
          <Box
            sx={{
              background:
                connectionStatus === "connected"
                  ? "green"
                  : connectionStatus === "disconnected"
                    ? "yellow"
                    : "red",
              width: 12,
              height: 12,
              borderRadius: "50%",
              position: "absolute",
              bottom: -3,
              right: -3,
            }}
          />
        </AgentIcon>
      </span>
    </Tooltip>
  );
}
