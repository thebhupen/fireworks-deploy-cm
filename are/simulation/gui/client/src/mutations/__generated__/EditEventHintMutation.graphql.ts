/**
 * @generated SignedSource<<32be1821c9914b95aa8d277f867936b0>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type EditEventHintMutation$variables = {
  eventId: string;
  hintContent: string;
  sessionId: string;
};
export type EditEventHintMutation$data = {
  readonly editHintContent: {
    readonly scenarioId: string;
  } | null | undefined;
};
export type EditEventHintMutation = {
  response: EditEventHintMutation$data;
  variables: EditEventHintMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "eventId"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "hintContent"
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
        "name": "eventId",
        "variableName": "eventId"
      },
      {
        "kind": "Variable",
        "name": "hintContent",
        "variableName": "hintContent"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "concreteType": "ScenarioForGraphQL",
    "kind": "LinkedField",
    "name": "editHintContent",
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
    "name": "EditEventHintMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "EditEventHintMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "fc6e29afe390decad56c1eb0d5aa117f",
    "id": null,
    "metadata": {},
    "name": "EditEventHintMutation",
    "operationKind": "mutation",
    "text": "mutation EditEventHintMutation(\n  $eventId: String!\n  $hintContent: String!\n  $sessionId: String!\n) {\n  editHintContent(eventId: $eventId, hintContent: $hintContent, sessionId: $sessionId) {\n    scenarioId\n  }\n}\n"
  }
};
})();

(node as any).hash = "59a8650ec63bb3555e7200b6343bb8c8";

export default node;
