/**
 * @generated SignedSource<<e907de4975e0831593bea20f8529a202>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type ExecuteAppToolMutation$variables = {
  appName: string;
  kwargs: string;
  sessionId: string;
  toolName: string;
};
export type ExecuteAppToolMutation$data = {
  readonly executeAppTool: {
    readonly appsStateJson: string;
    readonly returnValue: string | null | undefined;
  };
};
export type ExecuteAppToolMutation = {
  response: ExecuteAppToolMutation$data;
  variables: ExecuteAppToolMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "appName"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "kwargs"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v3 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "toolName"
},
v4 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "appName",
        "variableName": "appName"
      },
      {
        "kind": "Variable",
        "name": "kwargs",
        "variableName": "kwargs"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      },
      {
        "kind": "Variable",
        "name": "toolName",
        "variableName": "toolName"
      }
    ],
    "concreteType": "ExecuteAppToolResultForGraphQL",
    "kind": "LinkedField",
    "name": "executeAppTool",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "appsStateJson",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "returnValue",
        "storageKey": null
      }
    ],
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "ExecuteAppToolMutation",
    "selections": (v4/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v2/*: any*/),
      (v0/*: any*/),
      (v3/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Operation",
    "name": "ExecuteAppToolMutation",
    "selections": (v4/*: any*/)
  },
  "params": {
    "cacheID": "bbd9284c2213ad9567631ba7e953d098",
    "id": null,
    "metadata": {},
    "name": "ExecuteAppToolMutation",
    "operationKind": "mutation",
    "text": "mutation ExecuteAppToolMutation(\n  $sessionId: String!\n  $appName: String!\n  $toolName: String!\n  $kwargs: String!\n) {\n  executeAppTool(sessionId: $sessionId, appName: $appName, toolName: $toolName, kwargs: $kwargs) {\n    appsStateJson\n    returnValue\n  }\n}\n"
  }
};
})();

(node as any).hash = "e602d8a0e0639bbc292573c7b38c0042";

export default node;
