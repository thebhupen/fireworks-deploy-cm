/**
 * @generated SignedSource<<1886c8947cf0ea23bda55b2f82f75597>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type SendUserMessageToAgentMutation$variables = {
  attachments?: ReadonlyArray<ReadonlyArray<string>> | null | undefined;
  message: string;
  sessionId: string;
};
export type SendUserMessageToAgentMutation$data = {
  readonly sendUserMessageToAgent: string;
};
export type SendUserMessageToAgentMutation = {
  response: SendUserMessageToAgentMutation$data;
  variables: SendUserMessageToAgentMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "attachments"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "message"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v3 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "attachments",
        "variableName": "attachments"
      },
      {
        "kind": "Variable",
        "name": "message",
        "variableName": "message"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "sendUserMessageToAgent",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "SendUserMessageToAgentMutation",
    "selections": (v3/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v1/*: any*/),
      (v0/*: any*/),
      (v2/*: any*/)
    ],
    "kind": "Operation",
    "name": "SendUserMessageToAgentMutation",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "74f0a828c2f82eb75adac17c78ea0db6",
    "id": null,
    "metadata": {},
    "name": "SendUserMessageToAgentMutation",
    "operationKind": "mutation",
    "text": "mutation SendUserMessageToAgentMutation(\n  $message: String!\n  $attachments: [[String!]!]\n  $sessionId: String!\n) {\n  sendUserMessageToAgent(message: $message, attachments: $attachments, sessionId: $sessionId)\n}\n"
  }
};
})();

(node as any).hash = "272774c5b1fccd477554ccc220c6b8f2";

export default node;
