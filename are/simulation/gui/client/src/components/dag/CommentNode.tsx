// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CheckIcon from "@mui/icons-material/Check";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import {
  alpha,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  TextField,
  Tooltip,
  useTheme,
} from "@mui/material";
import { useReactFlow } from "@xyflow/react";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import { FIT_VIEW_OPTIONS } from "./FlowDag";
import { useNodeSelection } from "./NodeSelectionContext";

type CommentNodeProps = {
  id: string;
  data: {
    comment: string;
  };
};

export const COMMENT_NODE_BACKGROUND_COLOR = "#FFF176";
export const COMMENT_NODE_WIDTH = 300;
const COMMENT_NODE_HEIGHT = 200;

const CommentNode = ({ id, data }: CommentNodeProps) => {
  const { setNodes, fitView } = useReactFlow();
  const { scenario, setScenario } = useAppContext();
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const { selectNode } = useNodeSelection();
  const [comment, setComment] = useState(data.comment);
  const [isEditing, setIsEditing] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement>(null);
  const onChange = (
    event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>,
  ) => {
    setComment(event.currentTarget.value);
  };

  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus();
    }
  }, [isEditing]);

  useEffect(() => {
    setComment(scenario?.comment ?? "");
  }, [scenario]);

  useEffect(() => {
    if (!comment) {
      setIsEditing(true);
      inputRef.current?.focus();
    }
  }, [comment]);

  const handleSave = () => {
    if (scenario == null) {
      return;
    }
    setScenario({
      ...scenario!,
      comment: comment,
    });
  };

  const handleDelete = useCallback(() => {
    if (scenario == null) {
      return;
    }
    if (scenario.comment !== "") {
      setScenario({
        ...scenario!,
        comment: "",
      });
    }
    setNodes((nodes) => nodes.filter((node) => node.id !== id));
    setTimeout(() => {
      fitView(FIT_VIEW_OPTIONS);
    }, 200);
  }, [setNodes, id, scenario, setScenario, fitView]);

  return (
    <>
      <Card
        sx={{
          background: COMMENT_NODE_BACKGROUND_COLOR,
          width: COMMENT_NODE_WIDTH,
          minHeight: COMMENT_NODE_HEIGHT,
          borderRadius: "6px",
          border: "1px solid",
          borderColor: isEditing ? theme.palette.info.main : "transparent",
        }}
        elevation={6}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={() => selectNode(id)}
      >
        <CardContent
          sx={{
            background: "inherit",
            height: "100%",
            padding: 0,
            paddingBottom: "0 !important",
          }}
        >
          <TextField
            inputRef={inputRef}
            className={isEditing ? "nopan nodrag" : undefined}
            value={comment}
            onChange={onChange}
            disabled={!isEditing}
            placeholder="Enter a comment"
            multiline
            fullWidth
            focused={isEditing}
            sx={{
              "& .MuiInputBase-input.Mui-disabled": {
                WebkitTextFillColor: "black",
              },
              pointerEvents: isEditing ? "auto" : "none",
            }}
            slotProps={{
              input: {
                sx: {
                  color: "black",

                  minHeight: COMMENT_NODE_HEIGHT,
                  alignItems: "flex-start",
                },
              },
            }}
            onFocus={(e) =>
              e.currentTarget.setSelectionRange(
                e.currentTarget.value.length,
                e.currentTarget.value.length,
              )
            }
          />
          <AnimatePresence>
            {(isHovered || isEditing) && (
              <motion.div
                key={`comment`}
                style={{
                  position: "absolute",
                  bottom: "-32px",
                  right: 0,
                  justifyContent: "right",
                }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <ButtonGroup
                  variant="text"
                  size="small"
                  color="lightgrey"
                  sx={{
                    backgroundColor: alpha(
                      theme.palette.background.default,
                      0.8,
                    ),
                  }}
                >
                  <Tooltip
                    title={isEditing ? "Save Comment" : "EditIcon Comment"}
                  >
                    <span>
                      <Button
                        onClick={() => {
                          if (isEditing) {
                            handleSave();
                          }
                          setIsEditing(!isEditing);
                        }}
                      >
                        {isEditing ? (
                          <CheckIcon fontSize="small" />
                        ) : (
                          <EditIcon fontSize="small" />
                        )}
                      </Button>
                    </span>
                  </Tooltip>
                  <Tooltip title="DeleteIcon Comment">
                    <span>
                      <Button
                        onClick={() => {
                          handleDelete();
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </Button>
                    </span>
                  </Tooltip>
                </ButtonGroup>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </>
  );
};

export default CommentNode;
