/**
 * @generated SignedSource<<7bcb4622e5a1ddb96584c3be377f2b73>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type CapabilityTag = "Adaptability" | "Ambiguity" | "Collaboration" | "Execution" | "Exploration" | "Memory" | "Planning" | "PromptInjection" | "Safety" | "Search" | "Security" | "Time" | "UnitTest" | "Universe" | "%future added value";
export type TraceExporterQuery$variables = {
  annotationId?: string | null | undefined;
  annotatorName?: string | null | undefined;
  comment?: string | null | undefined;
  scenarioId: string;
  sessionId: string;
  tags?: ReadonlyArray<CapabilityTag> | null | undefined;
  validationDecision?: string | null | undefined;
};
export type TraceExporterQuery$data = {
  readonly activeScenario: {
    readonly scenarioId: string;
  } | null | undefined;
  readonly exportTraceData: string | null | undefined;
};
export type TraceExporterQuery = {
  response: TraceExporterQuery$data;
  variables: TraceExporterQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "annotationId"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "annotatorName"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "comment"
},
v3 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "scenarioId"
},
v4 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v5 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "tags"
},
v6 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "validationDecision"
},
v7 = {
  "kind": "Variable",
  "name": "sessionId",
  "variableName": "sessionId"
},
v8 = [
  {
    "alias": null,
    "args": [
      (v7/*: any*/)
    ],
    "concreteType": "ScenarioForGraphQL",
    "kind": "LinkedField",
    "name": "activeScenario",
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
  },
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "annotationId",
        "variableName": "annotationId"
      },
      {
        "kind": "Variable",
        "name": "annotatorName",
        "variableName": "annotatorName"
      },
      {
        "kind": "Variable",
        "name": "comment",
        "variableName": "comment"
      },
      {
        "kind": "Variable",
        "name": "scenarioId",
        "variableName": "scenarioId"
      },
      (v7/*: any*/),
      {
        "kind": "Variable",
        "name": "tags",
        "variableName": "tags"
      },
      {
        "kind": "Variable",
        "name": "validationDecision",
        "variableName": "validationDecision"
      }
    ],
    "kind": "ScalarField",
    "name": "exportTraceData",
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
      (v6/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "TraceExporterQuery",
    "selections": (v8/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v4/*: any*/),
      (v3/*: any*/),
      (v6/*: any*/),
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/),
      (v5/*: any*/)
    ],
    "kind": "Operation",
    "name": "TraceExporterQuery",
    "selections": (v8/*: any*/)
  },
  "params": {
    "cacheID": "5c205471262f125bc6b408f773990c97",
    "id": null,
    "metadata": {},
    "name": "TraceExporterQuery",
    "operationKind": "query",
    "text": "query TraceExporterQuery(\n  $sessionId: String!\n  $scenarioId: String!\n  $validationDecision: String\n  $annotationId: String\n  $annotatorName: String\n  $comment: String\n  $tags: [CapabilityTag!]\n) {\n  activeScenario(sessionId: $sessionId) {\n    scenarioId\n  }\n  exportTraceData(sessionId: $sessionId, scenarioId: $scenarioId, validationDecision: $validationDecision, annotationId: $annotationId, annotatorName: $annotatorName, comment: $comment, tags: $tags)\n}\n"
  }
};
})();

(node as any).hash = "20dd423736de0ffea8fee32aa7eeb4d2";

export default node;
