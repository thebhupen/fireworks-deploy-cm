// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { WebNav } from "../webnav/WebNav";
import ActionMessage from "./ActionMessage";
import AgentMessage from "./AgentMessage";
import ErrorMessage from "./ErrorMessage";
import FactsMessage from "./FactsMessage";
import ImageMessage from "./ImageMessage";
import PlanMessage from "./PlanMessage";
import ThoughtMessage from "./ThoughtMessage";
import UserMessage from "./UserMessage";

import DocumentMessage from "./DocumentMessage";
import { LLMInputOutputMessage } from "./LLMInputOutputMessage";
import { GroupType, Message } from "./createMessageList";

export function MessageComponent({
  message,
  showTimestamps,
  depth: _1 = 0,
  groupType: _2 = "ROOT",
}: {
  message: Message;
  showTimestamps: boolean;
  depth?: number;
  groupType?: GroupType;
}) {
  if (message.type === "WebNavigation") {
    return <WebNav stream={message.stream} key={message.id} />;
  } else if (message.type === "THOUGHT") {
    return <ThoughtMessage message={message} key={message.id} />;
  } else if (message.type === "ACTION") {
    return <ActionMessage message={message} key={message.id} />;
  } else if (message.type === "ERROR") {
    return <ErrorMessage message={message} key={message.id} />;
  } else if (message.type === "Image") {
    return <ImageMessage key={message.id} message={message} />;
  } else if (message.type === "Document") {
    return <DocumentMessage key={message.id} message={message} />;
  } else if (message.type === "FACTS") {
    return <FactsMessage key={message.id} message={message} />;
  } else if (message.type === "PLAN") {
    return <PlanMessage key={message.id} message={message} />;
  } else if (message.type === "OBSERVATION") {
    // We will later need this for the progress sidebar
    return null;
  } else if (message.type === "GROUP") {
    return (
      <>
        {message.messages.map((m) => (
          <MessageComponent
            key={m.id}
            message={m}
            showTimestamps={showTimestamps}
            depth={message.depth}
            groupType={message.groupType}
          />
        ))}
      </>
    );
  } else if (message.type === "LLMInputOutput") {
    return <LLMInputOutputMessage key={message.id} message={message} />;
  } else if (message.sender?.toUpperCase() === "USER") {
    return (
      <UserMessage
        message={message}
        key={message.id}
        showTimestamps={showTimestamps}
      />
    );
  } else {
    return (
      <AgentMessage
        message={message}
        key={message.id}
        showTimestamps={showTimestamps}
      />
    );
  }
}
