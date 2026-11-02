/**
 * @generated SignedSource<<1e5a8c13e81940598c23a6cca8aac016>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type SetAgentConfigMutation$variables = {
  agentConfig?: any | null | undefined;
  sessionId: string;
};
export type SetAgentConfigMutation$data = {
  readonly setAgentConfig: any | null | undefined;
};
export type SetAgentConfigMutation = {
  response: SetAgentConfigMutation$data;
  variables: SetAgentConfigMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "agentConfig"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v2 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "agentConfig",
        "variableName": "agentConfig"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "setAgentConfig",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "SetAgentConfigMutation",
    "selections": (v2/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v1/*: any*/),
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "SetAgentConfigMutation",
    "selections": (v2/*: any*/)
  },
  "params": {
    "cacheID": "08a234584fe8c721c6fb534c11a8d95c",
    "id": null,
    "metadata": {},
    "name": "SetAgentConfigMutation",
    "operationKind": "mutation",
    "text": "mutation SetAgentConfigMutation(\n  $sessionId: String!\n  $agentConfig: JSON\n) {\n  setAgentConfig(sessionId: $sessionId, agentConfig: $agentConfig)\n}\n"
  }
};
})();

(node as any).hash = "6735e6c12817cef548df86c05d20283b";

export default node;
