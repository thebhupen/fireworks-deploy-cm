// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CloseIcon from "@mui/icons-material/Close";
import {
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  styled,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
} from "@mui/material";
import React from "react";

interface DetailsDialogProps {
  properties?: Record<string, React.ReactNode> | null;
  content?: React.ReactNode | null;
  actions?: React.ReactNode;
  isOpen: boolean;
  onClose: () => void;
  icon?: React.ReactNode;
  title: React.ReactNode | string;
}

const DetailsTable = styled(Table)({
  padding: 0,
});

/**
 * DetailsDialog component displays a dialog with detailed information.
 *
 * @param {DetailsDialogProps} props - The properties object.
 * @param {Record<string, React.ReactNode>} props.properties - The properties to display in the dialog.
 * @param {React.ReactNode} [props.content] - Optional content to display in the dialog.
 * @param {React.ReactNode} [props.actions] - Optional actions to display in the dialog.
 * @param {boolean} props.isOpen - Boolean indicating if the dialog is open.
 * @param {() => void} props.onClose - Function to call when the dialog is closed.
 * @param {React.ReactNode} [props.icon] - Optional icon to display in the dialog title.
 * @param {string} props.title - Title of the dialog.
 *
 * @returns {JSX.Element} A dialog component displaying details.
 */
const DetailsDialog: React.FC<DetailsDialogProps> = ({
  properties,
  content,
  actions,
  isOpen,
  onClose,
  icon,
  title,
}: DetailsDialogProps) => {
  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="md">
      <DialogTitle>
        <Stack direction="row" alignItems={"center"}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              {icon}
              <span>{title}</span>
            </Stack>
          </Typography>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={1}>
          {!!properties && (
            <Card>
              <CardContent>
                <TableContainer>
                  <DetailsTable size="small">
                    <TableBody>
                      {Object.entries(properties).map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell style={{ verticalAlign: "top" }}>
                            <Typography component="span">{key}</Typography>
                          </TableCell>
                          <TableCell align="left">
                            <Typography component="span">{value}</Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </DetailsTable>
                </TableContainer>
              </CardContent>
            </Card>
          )}
          {content}
        </Stack>
      </DialogContent>
      <DialogActions>{actions}</DialogActions>
    </Dialog>
  );
};

export default DetailsDialog;
