/**
 * @generated SignedSource<<061693596baeb40d78ff2776ae36ee21>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type EventTimeComparator = "EQUAL" | "GREATER_THAN" | "LESS_THAN" | "%future added value";
export type EventType = "AGENT" | "CONDITION" | "ENV" | "STOP" | "USER" | "VALIDATION" | "%future added value";
export type AddScenarioEventMutation$variables = {
  app: string;
  eventRelativeTime?: number | null | undefined;
  eventTime?: number | null | undefined;
  eventTimeComparator?: EventTimeComparator | null | undefined;
  eventType: EventType;
  function: string;
  parameters: string;
  predecessorEventIds: ReadonlyArray<string>;
  sessionId: string;
};
export type AddScenarioEventMutation$data = {
  readonly addScenarioEvent: string;
};
export type AddScenarioEventMutation = {
  response: AddScenarioEventMutation$data;
  variables: AddScenarioEventMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "app"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventRelativeTime"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventTime"
},
v3 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventTimeComparator"
},
v4 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventType"
},
v5 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "function"
},
v6 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "parameters"
},
v7 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "predecessorEventIds"
},
v8 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v9 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "app",
        "variableName": "app"
      },
      {
        "kind": "Variable",
        "name": "eventRelativeTime",
        "variableName": "eventRelativeTime"
      },
      {
        "kind": "Variable",
        "name": "eventTime",
        "variableName": "eventTime"
      },
      {
        "kind": "Variable",
        "name": "eventTimeComparator",
        "variableName": "eventTimeComparator"
      },
      {
        "kind": "Variable",
        "name": "eventType",
        "variableName": "eventType"
      },
      {
        "kind": "Variable",
        "name": "function",
        "variableName": "function"
      },
      {
        "kind": "Variable",
        "name": "parameters",
        "variableName": "parameters"
      },
      {
        "kind": "Variable",
        "name": "predecessorEventIds",
        "variableName": "predecessorEventIds"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "addScenarioEvent",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/),
      (v4/*: any*/),
      (v5/*: any*/),
      (v6/*: any*/),
      (v7/*: any*/),
      (v8/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "AddScenarioEventMutation",
    "selections": (v9/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v8/*: any*/),
      (v0/*: any*/),
      (v5/*: any*/),
      (v6/*: any*/),
      (v7/*: any*/),
      (v4/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/)
    ],
    "kind": "Operation",
    "name": "AddScenarioEventMutation",
    "selections": (v9/*: any*/)
  },
  "params": {
    "cacheID": "f42daca134e7392f5274af497c876872",
    "id": null,
    "metadata": {},
    "name": "AddScenarioEventMutation",
    "operationKind": "mutation",
    "text": "mutation AddScenarioEventMutation(\n  $sessionId: String!\n  $app: String!\n  $function: String!\n  $parameters: String!\n  $predecessorEventIds: [String!]!\n  $eventType: EventType!\n  $eventRelativeTime: Float\n  $eventTime: Float\n  $eventTimeComparator: EventTimeComparator\n) {\n  addScenarioEvent(sessionId: $sessionId, app: $app, function: $function, parameters: $parameters, predecessorEventIds: $predecessorEventIds, eventType: $eventType, eventRelativeTime: $eventRelativeTime, eventTime: $eventTime, eventTimeComparator: $eventTimeComparator)\n}\n"
  }
};
})();

(node as any).hash = "6f7d9b59ccd4f20d20f80ecc6ed9d76d";

export default node;
