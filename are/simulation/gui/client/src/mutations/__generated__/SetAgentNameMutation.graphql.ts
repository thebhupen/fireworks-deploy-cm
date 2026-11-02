/**
 * @generated SignedSource<<e38ddecccf4efe54e31da67d5bc15fd1>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type SetAgentNameMutation$variables = {
  agentId?: string | null | undefined;
  sessionId: string;
};
export type SetAgentNameMutation$data = {
  readonly setAgentName: any | null | undefined;
};
export type SetAgentNameMutation = {
  response: SetAgentNameMutation$data;
  variables: SetAgentNameMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "agentId"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "sessionId"
  }
],
v1 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "agentId",
        "variableName": "agentId"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "setAgentName",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "SetAgentNameMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "SetAgentNameMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "a2a412409fad3f518972c2a56caf7702",
    "id": null,
    "metadata": {},
    "name": "SetAgentNameMutation",
    "operationKind": "mutation",
    "text": "mutation SetAgentNameMutation(\n  $agentId: String\n  $sessionId: String!\n) {\n  setAgentName(agentId: $agentId, sessionId: $sessionId)\n}\n"
  }
};
})();

(node as any).hash = "860d75c3aee5ce8481b5489464f1dc3f";

export default node;
