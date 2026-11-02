/**
 * @generated SignedSource<<b4c18774ec42145c24c4e4a37ab79ad4>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type StopMutation$variables = {
  sessionId: string;
};
export type StopMutation$data = {
  readonly stop: {
    readonly scenarioId: string;
  } | null | undefined;
};
export type StopMutation = {
  response: StopMutation$data;
  variables: StopMutation$variables;
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
    "name": "stop",
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
    "name": "StopMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "StopMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "2ac97b9f3b61d144e59c033e651cbbe5",
    "id": null,
    "metadata": {},
    "name": "StopMutation",
    "operationKind": "mutation",
    "text": "mutation StopMutation(\n  $sessionId: String!\n) {\n  stop(sessionId: $sessionId) {\n    scenarioId\n  }\n}\n"
  }
};
})();

(node as any).hash = "aab3030acfc322aaa07570ae871b6c49";

export default node;
