/**
 * @generated SignedSource<<0422ab46f110a6c4b37ee8cd406b60ce>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type EventTimeComparator = "EQUAL" | "GREATER_THAN" | "LESS_THAN" | "%future added value";
export type EventType = "AGENT" | "CONDITION" | "ENV" | "STOP" | "USER" | "VALIDATION" | "%future added value";
export type EditScenarioEventMutation$variables = {
  app: string;
  eventId: string;
  eventRelativeTime?: number | null | undefined;
  eventTime?: number | null | undefined;
  eventTimeComparator?: EventTimeComparator | null | undefined;
  eventType: EventType;
  function: string;
  parameters: string;
  predecessorEventIds: ReadonlyArray<string>;
  sessionId: string;
};
export type EditScenarioEventMutation$data = {
  readonly editScenarioEvent: string;
};
export type EditScenarioEventMutation = {
  response: EditScenarioEventMutation$data;
  variables: EditScenarioEventMutation$variables;
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
  "name": "eventId"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventRelativeTime"
},
v3 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventTime"
},
v4 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventTimeComparator"
},
v5 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "eventType"
},
v6 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "function"
},
v7 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "parameters"
},
v8 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "predecessorEventIds"
},
v9 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v10 = [
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
        "name": "eventId",
        "variableName": "eventId"
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
    "name": "editScenarioEvent",
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
      (v8/*: any*/),
      (v9/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "EditScenarioEventMutation",
    "selections": (v10/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v9/*: any*/),
      (v0/*: any*/),
      (v6/*: any*/),
      (v7/*: any*/),
      (v1/*: any*/),
      (v5/*: any*/),
      (v8/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/),
      (v4/*: any*/)
    ],
    "kind": "Operation",
    "name": "EditScenarioEventMutation",
    "selections": (v10/*: any*/)
  },
  "params": {
    "cacheID": "74ecf0dc8bf57a28d813116166a97f3d",
    "id": null,
    "metadata": {},
    "name": "EditScenarioEventMutation",
    "operationKind": "mutation",
    "text": "mutation EditScenarioEventMutation(\n  $sessionId: String!\n  $app: String!\n  $function: String!\n  $parameters: String!\n  $eventId: String!\n  $eventType: EventType!\n  $predecessorEventIds: [String!]!\n  $eventRelativeTime: Float\n  $eventTime: Float\n  $eventTimeComparator: EventTimeComparator\n) {\n  editScenarioEvent(sessionId: $sessionId, app: $app, function: $function, parameters: $parameters, eventId: $eventId, eventType: $eventType, predecessorEventIds: $predecessorEventIds, eventRelativeTime: $eventRelativeTime, eventTime: $eventTime, eventTimeComparator: $eventTimeComparator)\n}\n"
  }
};
})();

(node as any).hash = "5a4bf2da6faeb3c12ef525d94f021f53";

export default node;
