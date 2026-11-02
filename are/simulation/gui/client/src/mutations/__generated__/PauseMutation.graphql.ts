/**
 * @generated SignedSource<<33e3bbdeb3026a2599ac0d0f134330e2>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type PauseMutation$variables = {
  sessionId: string;
};
export type PauseMutation$data = {
  readonly pause: {
    readonly scenarioId: string;
  } | null | undefined;
};
export type PauseMutation = {
  response: PauseMutation$data;
  variables: PauseMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
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
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "concreteType": "ScenarioForGraphQL",
    "kind": "LinkedField",
    "name": "pause",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "scenarioId",
        "storageKey": null
      }
    ],
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "PauseMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "PauseMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "0799d19ed9318ecdbc2837d47174107e",
    "id": null,
    "metadata": {},
    "name": "PauseMutation",
    "operationKind": "mutation",
    "text": "mutation PauseMutation(\n  $sessionId: String!\n) {\n  pause(sessionId: $sessionId) {\n    scenarioId\n  }\n}\n"
  }
};
})();

(node as any).hash = "842de1b5b59efaf159c2e838c4e33ba3";

export default node;
