// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface MessageV2 {
  sender_id: string;
  sender?: string;
  message_id?: string;
  timestamp?: number;
  content?: string;
}

export interface ConversationV2 {
  participant_ids: string[];
  participants?: string[];
  messages?: MessageV2[];
  title?: string | null;
  conversation_id?: string;
  last_updated?: number;
}

export enum MessagingAppMode {
  MESSENGER = "MESSENGER",
  WHATSAPP = "WHATSAPP",
}

export interface MessagingApp {
  app_name?: AppName;
  current_user_id?: string | null;
  current_user_name?: string | null;
  name?: string | null;
  mode: MessagingAppMode;
  id_to_name: Record<string, string>;
  name_to_id: Record<string, string>;
  conversations: Record<string, ConversationV2>;
  messages_view_limit: number;
  conversation_view_limit: number;
}
