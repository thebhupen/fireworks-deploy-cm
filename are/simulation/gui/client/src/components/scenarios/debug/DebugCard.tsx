// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  Card,
  CardActions,
  CardContent,
  CardHeader,
  Typography,
  useTheme,
} from "@mui/material";

const DEBUG_VIEW_HEIGHT = "100%";

interface DebugCardProps {
  title: string;
  children: React.ReactNode;
  menu?: React.ReactNode;
  actions?: React.ReactNode;
}

/**
 * DebugCard panel for the debug view that displays a card with a header, content, and optional actions.
 *
 * @param {string} title - The title to be displayed in the card header.
 * @param {React.ReactNode} children - The content to be displayed within the card.
 * @param {React.ReactNode} [actions] - Optional actions to be displayed in the card footer.
 */
const DebugCard = ({ title, menu, actions, children }: DebugCardProps) => {
  const theme = useTheme();
  return (
    <Card
      elevation={3}
      sx={{
        width: "100%",
        height: DEBUG_VIEW_HEIGHT,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        border: `1px solid ${theme.palette.divider}`,
      }}
    >
      <CardHeader
        title={
          <Typography
            variant="subtitle1"
            color="text.secondary"
            fontSize={"16px"}
          >
            {title}
          </Typography>
        }
        action={menu}
      />
      <CardContent
        sx={{
          display: "flex",
          flexGrow: 1,
          overflow: "auto",
          "&:last-child": {
            paddingBottom: 1,
          },
        }}
      >
        {children}
      </CardContent>
      {actions && (
        <CardActions
          sx={{
            margin: 1,
            height: "64px",
            justifyContent: "center",
            padding: 1,
          }}
        >
          {actions}
        </CardActions>
      )}
    </Card>
  );
};

export default DebugCard;
