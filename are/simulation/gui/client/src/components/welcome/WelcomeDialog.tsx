// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import Assessment from "@mui/icons-material/Assessment";
import GitHubIcon from "@mui/icons-material/GitHub";
import HubIcon from "@mui/icons-material/Hub";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Link,
  List,
  ListItem,
  Stack,
  Typography,
} from "@mui/material";
import {
  ARXIV_URL,
  DOC_URL,
  GITHUB_REPO_URL,
  HF_DATASET_URL,
} from "../../utils/const";

export const WelcomeDialog = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}): React.ReactNode => {
  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            width: "650px",
          },
        },
      }}
    >
      <DialogTitle>Welcome to Meta Agents Research Environments</DialogTitle>
      <DialogContent>
        <Stack spacing={3}>
          <Typography fontSize={16}>
            This tool was built to help you explore the Gaia2 benchmark and
            associated environments, scenarios, and agent traces.
          </Typography>
          <List
            sx={{
              listStyleType: "disc",
              pl: 2,
              "& .MuiListItem-root": {
                display: "list-item",
              },
            }}
          >
            <ListItem>
              <Typography fontSize={16}>
                <strong>Playground:</strong> Explore a demo environment
                featuring a mobile device, its apps, and their data. You can ask
                an agent to execute tasks and explore the traces in the
                execution panel.
              </Typography>
            </ListItem>
            <ListItem>
              <Typography fontSize={16}>
                <strong>Scenarios:</strong> Explore Gaia2 environment and
                scenarios. Reload and visualize agent traces for Gaia2
                scenarios.
              </Typography>
            </ListItem>
          </List>
          <Stack spacing={1}>
            <Typography variant="h6">Documentation</Typography>
            <Typography fontSize={16}>
              You can learn more about how best to create environments and
              scenarios in Meta Agents Research Environments in our{" "}
              <Link href={DOC_URL} target="_blank">
                official documentation
              </Link>
              .
            </Typography>
            <Stack direction={"row"} spacing={1}>
              <Chip
                icon={<GitHubIcon />}
                label="GitHub"
                href={GITHUB_REPO_URL}
                clickable
                component="a"
                target="_blank"
              />
              <Chip
                icon={<HubIcon fontSize="small" />}
                label="Gaia2"
                component="a"
                href={HF_DATASET_URL}
                target="_blank"
                clickable
                sx={{
                  pl: 0.5,
                }}
              />
              <Chip
                icon={<Assessment fontSize="small" />}
                label="Paper"
                href={ARXIV_URL}
                clickable
                target="_blank"
                component="a"
                sx={{
                  pl: 0.5,
                }}
              />
            </Stack>
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Box
          sx={{
            display: "flex",
            justifyContent: "right",
            alignItems: "center",
            width: "100%",
            marginX: 2,
            marginBottom: 1,
          }}
        >
          <Button variant="contained" color="primary" onClick={onClose}>
            Got it
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
};
