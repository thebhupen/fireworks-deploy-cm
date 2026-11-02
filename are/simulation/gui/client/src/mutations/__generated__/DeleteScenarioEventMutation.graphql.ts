/**
 * @generated SignedSource<<c7dd315201065104ca940783ab4fe65d>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type DeleteScenarioEventMutation$variables = {
  eventId: string;
  sessionId: string;
};
export type DeleteScenarioEventMutation$data = {
  readonly deleteScenarioEvent: any | null | undefined;
};
export type DeleteScenarioEventMutation = {
  response: DeleteScenarioEventMutation$data;
  variables: DeleteScenarioEventMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventId"
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
        "name": "eventId",
        "variableName": "eventId"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "deleteScenarioEvent",
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
    "name": "DeleteScenarioEventMutation",
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
    "name": "DeleteScenarioEventMutation",
    "selections": (v2/*: any*/)
  },
  "params": {
    "cacheID": "91d690f4bf87284a84b0e004ec8bdbb6",
    "id": null,
    "metadata": {},
    "name": "DeleteScenarioEventMutation",
    "operationKind": "mutation",
    "text": "mutation DeleteScenarioEventMutation(\n  $sessionId: String!\n  $eventId: String!\n) {\n  deleteScenarioEvent(sessionId: $sessionId, eventId: $eventId)\n}\n"
  }
};
})();

(node as any).hash = "56d2ab86dcb05a795b888620ab58a3a7";

export default node;
