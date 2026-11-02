// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { Button, ButtonGroup, IconButton } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import RestartAltIcon from "@mui/icons-material/RestartAlt";

export type WebNavFrame = {
  step_response: string;
  step_screenshot: string;
  timestamp: number;
};

export type WebNavStream = {
  task: string;
  frames: ReadonlyArray<WebNavFrame>;
};

const FRAME_SELECTOR_HEIGHT = 60;

export function WebNav(props: { stream: WebNavStream }): React.ReactNode {
  const { stream } = props;
  const { task, frames: allFrames } = stream;

  // Skip the last frame since it is a gif of all the others
  const frames = allFrames.slice(0, -1);
  const timeRef = React.useRef(0);
  const [index, setIndex] = React.useState(frames.length - 1);
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [playbackSpeed, setPlaybackSpeed] = React.useState<1 | 2 | 3>(1);

  const currentFrame = frames[index];

  React.useEffect(() => {
    if (isPlaying) {
      return;
    } else {
      setIndex((index) => {
        if (index === frames.length - 2) {
          return frames.length - 1;
        } else {
          return index;
        }
      });
    }
  }, [isPlaying, frames.length]);

  React.useEffect(() => {
    if (isPlaying) {
      let interval: number | null = null;
      const onFrame = (timestamp: number) => {
        if (timeRef.current === 0) {
          timeRef.current = timestamp / 1000;
        }

        while (timeRef.current + 1 / playbackSpeed < timestamp / 1000) {
          timeRef.current += 1 / playbackSpeed;

          if (!isPlaying) {
            // Let's skip the loop since we are not playing
            continue;
          } else if (index >= frames.length - 1) {
            // End the frames
            setIsPlaying(false);
          } else {
            // Move to the next frame
            setIndex((index) => (index + 1) % frames.length);
          }
        }

        interval = requestAnimationFrame(onFrame);
      };

      onFrame(0);

      return () => {
        if (interval !== null) {
          cancelAnimationFrame(interval);
        }
      };
    }
  }, [isPlaying, playbackSpeed, frames.length, index]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "stretch",
        gap: 12,
        width: "61%",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
        }}
      >
        <p
          style={{
            margin: 0,
          }}
        >
          {task}
        </p>
        <ButtonGroup variant="contained" size="small">
          <IconButton
            onClick={() => {
              if (index === frames.length - 1) {
                setIndex(0);
              }
              if (isPlaying) {
                setIsPlaying(false);
              } else {
                timeRef.current = 0;
                setIsPlaying(true);
              }
            }}
            size="small"
          >
            {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
          </IconButton>
          <Button
            onClick={() => {
              if (playbackSpeed === 1) {
                setPlaybackSpeed(2);
              } else if (playbackSpeed === 2) {
                setPlaybackSpeed(3);
              } else if (playbackSpeed === 3) {
                setPlaybackSpeed(1);
              }
            }}
            size="small"
          >
            <span style={{ fontSize: 14 }}>{`x${playbackSpeed}`}</span>
          </Button>
          <IconButton onClick={() => setIndex(0)} size="small">
            <RestartAltIcon />
          </IconButton>
        </ButtonGroup>
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "stretch",
          alignItems: "stretch",
          marginLeft: "auto",
          marginRight: "auto",
          position: "relative",
        }}
      >
        <div
          style={{
            border: `1px solid #ABB3BF`,
            borderRadius: 8,
            overflow: "hidden",
            boxShadow: `0 0 1px 1px #ABB3BF`,
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
          }}
        >
          <img
            alt={currentFrame?.step_response}
            style={{
              width: "100%",
              objectFit: "contain",
            }}
            src={currentFrame?.step_screenshot}
          />
        </div>
      </div>
      {
        <>
          <div
            style={{
              position: "relative",
              height: FRAME_SELECTOR_HEIGHT,
            }}
          >
            <input
              style={{
                height: FRAME_SELECTOR_HEIGHT,
                width: "100%",
                opacity: 0,
                cursor: "pointer",
              }}
              type="range"
              min={0}
              max={frames.length - 1}
              value={index}
              onChange={(e) => {
                setIndex(parseInt(e.target.value));
              }}
            />
            <div
              style={{
                pointerEvents: "none",
                display: "flex",
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                justifyContent: "space-around",
                backgroundColor: "rgba(0,0,0,0.2)",
                borderRadius: 4,
              }}
            >
              {frames.map((frame, i) => {
                return (
                  <div
                    key={i}
                    style={{
                      position: "relative",
                      maxWidth: `calc(100% / ${frames.length})`,
                    }}
                  >
                    <img
                      alt={frame.step_response}
                      style={{
                        border: `1px solid #ABB3BF`,
                        userSelect: "none",
                        borderRadius: 4,
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                      }}
                      width={100}
                      src={frame.step_screenshot}
                    />
                    <div
                      style={{
                        position: "absolute",
                        height: 16,
                        width: 16,
                        backgroundColor: "#2D72D2",
                        borderRadius: "50%",
                        bottom: 4,
                        right: 4,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <span style={{ fontSize: 10 }}>{i + 1}</span>
                    </div>
                  </div>
                );
              })}
            </div>
            <div
              style={{
                pointerEvents: "none",
                border: `2px solid #2D72D2`,
                position: "absolute",
                top: 0,
                bottom: 0,
                borderRadius: 4,
                width: `calc(100% / ${frames.length})`,
                transform: `translateX(${index * 100}%)`,
                transition: "transform 0.1s ease-in-out",
              }}
            />
          </div>
        </>
      }
    </div>
  );
}
