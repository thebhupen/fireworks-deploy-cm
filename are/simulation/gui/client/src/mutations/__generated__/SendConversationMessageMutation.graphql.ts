/**
 * @generated SignedSource<<c189c16c8cc7cd49faf06ce0885e9d90>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type SendConversationMessageMutation$variables = {
  conversationId: string;
  message: string;
  messagingAppName: string;
  sender: string;
  sessionId: string;
};
export type SendConversationMessageMutation$data = {
  readonly sendConversationMessage: boolean;
};
export type SendConversationMessageMutation = {
  response: SendConversationMessageMutation$data;
  variables: SendConversationMessageMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "conversationId"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "message"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "messagingAppName"
},
v3 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sender"
},
v4 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v5 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "conversationId",
        "variableName": "conversationId"
      },
      {
        "kind": "Variable",
        "name": "message",
        "variableName": "message"
      },
      {
        "kind": "Variable",
        "name": "messagingAppName",
        "variableName": "messagingAppName"
      },
      {
        "kind": "Variable",
        "name": "sender",
        "variableName": "sender"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "sendConversationMessage",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/),
      (v4/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "SendConversationMessageMutation",
    "selections": (v5/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v4/*: any*/),
      (v2/*: any*/),
      (v0/*: any*/),
      (v3/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Operation",
    "name": "SendConversationMessageMutation",
    "selections": (v5/*: any*/)
  },
  "params": {
    "cacheID": "3b797764d0afe641f5b272c4c3bc6cca",
    "id": null,
    "metadata": {},
    "name": "SendConversationMessageMutation",
    "operationKind": "mutation",
    "text": "mutation SendConversationMessageMutation(\n  $sessionId: String!\n  $messagingAppName: String!\n  $conversationId: String!\n  $sender: String!\n  $message: String!\n) {\n  sendConversationMessage(sessionId: $sessionId, messagingAppName: $messagingAppName, conversationId: $conversationId, sender: $sender, message: $message)\n}\n"
  }
};
})();

(node as any).hash = "62b955dd1ef4379f6975fb697a780817";

export default node;
