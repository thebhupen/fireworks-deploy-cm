/**
 * @generated SignedSource<<8fac37e4845d588366e5a02b38581de2>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type EditScenarioDurationMutation$variables = {
  duration?: number | null | undefined;
  sessionId: string;
};
export type EditScenarioDurationMutation$data = {
  readonly editScenarioDuration: number | null | undefined;
};
export type EditScenarioDurationMutation = {
  response: EditScenarioDurationMutation$data;
  variables: EditScenarioDurationMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "duration"
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
        "name": "duration",
        "variableName": "duration"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "editScenarioDuration",
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
    "name": "EditScenarioDurationMutation",
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
    "name": "EditScenarioDurationMutation",
    "selections": (v2/*: any*/)
  },
  "params": {
    "cacheID": "cd7eefee5dee9dfb2b631c8136b6a221",
    "id": null,
    "metadata": {},
    "name": "EditScenarioDurationMutation",
    "operationKind": "mutation",
    "text": "mutation EditScenarioDurationMutation(\n  $sessionId: String!\n  $duration: Float\n) {\n  editScenarioDuration(sessionId: $sessionId, duration: $duration)\n}\n"
  }
};
})();

(node as any).hash = "edff0946e5968e7a8e5a2e71d9f65f45";

export default node;
