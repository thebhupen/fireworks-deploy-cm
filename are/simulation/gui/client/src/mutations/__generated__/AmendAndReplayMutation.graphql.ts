/**
 * @generated SignedSource<<cd2b279f1bc18ef07a83c143ec9d7301>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type AmendAndReplayMutation$variables = {
  content: string;
  logId: string;
  sessionId: string;
};
export type AmendAndReplayMutation$data = {
  readonly amendAndReplay: {
    readonly scenarioId: string;
  } | null | undefined;
};
export type AmendAndReplayMutation = {
  response: AmendAndReplayMutation$data;
  variables: AmendAndReplayMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "content"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "logId"
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
        "name": "content",
        "variableName": "content"
      },
      {
        "kind": "Variable",
        "name": "logId",
        "variableName": "logId"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "concreteType": "ScenarioForGraphQL",
    "kind": "LinkedField",
    "name": "amendAndReplay",
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
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "AmendAndReplayMutation",
    "selections": (v3/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v2/*: any*/),
      (v1/*: any*/),
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "AmendAndReplayMutation",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "efca69a9a1db6227e36b20cd6b77dd79",
    "id": null,
    "metadata": {},
    "name": "AmendAndReplayMutation",
    "operationKind": "mutation",
    "text": "mutation AmendAndReplayMutation(\n  $sessionId: String!\n  $logId: String!\n  $content: String!\n) {\n  amendAndReplay(sessionId: $sessionId, logId: $logId, content: $content) {\n    scenarioId\n  }\n}\n"
  }
};
})();

(node as any).hash = "c4d3eed1dafd96e698e8c04caf54afe9";

export default node;
