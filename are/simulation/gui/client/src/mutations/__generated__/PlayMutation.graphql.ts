/**
 * @generated SignedSource<<0506b4f8d3b478e2929ccfde8984607e>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type PlayMutation$variables = {
  sessionId: string;
};
export type PlayMutation$data = {
  readonly play: {
    readonly scenarioId: string;
  } | null | undefined;
};
export type PlayMutation = {
  response: PlayMutation$data;
  variables: PlayMutation$variables;
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
    "name": "play",
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
    "name": "PlayMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "PlayMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "868791e97bad59d00e8a86fbbf0ec180",
    "id": null,
    "metadata": {},
    "name": "PlayMutation",
    "operationKind": "mutation",
    "text": "mutation PlayMutation(\n  $sessionId: String!\n) {\n  play(sessionId: $sessionId) {\n    scenarioId\n  }\n}\n"
  }
};
})();

(node as any).hash = "5bf62066bf858ecf124b17b383dc0233";

export default node;
