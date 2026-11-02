// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import SearchIcon from "@mui/icons-material/Search";
import { Box, FormControl, Stack, TextField, Typography } from "@mui/material";
import * as React from "react";
import { useMemo } from "react";
import ConversationSection from "./ConversationSection";
import { MessagingApp } from "./types";

// Function to map IDs to names with ID in parentheses
function mapIdToName(id: string, idToNameMap: { [key: string]: string }) {
  const name = idToNameMap[id];
  return name ? `${name} (${id})` : id;
}

function MessagesTab({ state }: { state: MessagingApp }): React.ReactNode {
  const NO_CONVERSATIONS_FOUND = "No conversations found.";

  // We only add these fields in case of the newer version of MessagingApp - V2
  // As we have Ids everywhere, we need to map them to names
  if (state?.id_to_name) {
    // Process conversations
    Object.keys(state.conversations).forEach((conversationId) => {
      const conversation = state.conversations[conversationId];

      // Add participants field to each conversation
      conversation.participants = conversation.participant_ids.map((id) =>
        mapIdToName(id, state.id_to_name),
      );

      // Add sender field to each message
      conversation.messages?.forEach((message) => {
        message.sender = mapIdToName(message.sender_id, state.id_to_name);
      });
    });
  }

  const conversations = useMemo(() => state.conversations, [state]);

  const [searchTerm, setSearchTerm] = React.useState("");

  const filteredConversations = useMemo(() => {
    return Object.entries(conversations)
      .sort(([, a], [, b]) => (b.last_updated ?? 0) - (a.last_updated ?? 0))
      .filter(([id, conversation]) => {
        const conversationString = JSON.stringify(conversation).toLowerCase();
        const searchTermLower = searchTerm.toLowerCase();
        return (
          id.includes(searchTermLower) ||
          conversationString.includes(searchTermLower)
        );
      });
  }, [conversations, searchTerm]);

  if (!state || !conversations || Object.keys(conversations).length === 0) {
    return <div>{NO_CONVERSATIONS_FOUND}</div>;
  }

  const sections = filteredConversations.map(([id, conversation]) => {
    return (
      <ConversationSection
        data={conversation}
        participants={conversation.participants ?? []}
        messagingAppName={state.app_name!}
        currentUserId={state.current_user_id}
        key={id}
      />
    );
  });

  return (
    <Stack spacing={1}>
      <Typography variant="h6">
        Conversations: {filteredConversations.length}
      </Typography>
      <FormControl fullWidth>
        <TextField
          placeholder={`Search conversations...`}
          onChange={(e) => setSearchTerm(e.target.value)}
          slotProps={{
            input: {
              startAdornment: <SearchIcon />,
            },
          }}
          size="small"
          value={searchTerm}
        />
      </FormControl>
      <Box>
        {sections.length > 0 ? sections : <h4>No conversations found.</h4>}
      </Box>
    </Stack>
  );
}
export default MessagesTab;
