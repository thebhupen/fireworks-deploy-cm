/**
 * @generated SignedSource<<30ab7f5e54cb75dab24fcd34bc61ec1f>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type LoadMutation$variables = {
  sessionId: string;
};
export type LoadMutation$data = {
  readonly load: {
    readonly scenarioId: string;
  } | null | undefined;
};
export type LoadMutation = {
  response: LoadMutation$data;
  variables: LoadMutation$variables;
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
    "name": "load",
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
    "name": "LoadMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "LoadMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "c2d543134b02ed14e956f51f7c9d4490",
    "id": null,
    "metadata": {},
    "name": "LoadMutation",
    "operationKind": "mutation",
    "text": "mutation LoadMutation(\n  $sessionId: String!\n) {\n  load(sessionId: $sessionId) {\n    scenarioId\n  }\n}\n"
  }
};
})();

(node as any).hash = "e9cd1d9c9845c231a177407c37246a9b";

export default node;
