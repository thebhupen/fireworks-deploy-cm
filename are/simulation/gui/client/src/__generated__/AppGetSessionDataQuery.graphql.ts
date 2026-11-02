/**
 * @generated SignedSource<<076c3b24fd4a3b178d1cb348607bc3ea>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type CapabilityTag = "Adaptability" | "Ambiguity" | "Collaboration" | "Execution" | "Exploration" | "Memory" | "Planning" | "PromptInjection" | "Safety" | "Search" | "Security" | "Time" | "UnitTest" | "Universe" | "%future added value";
export type AppGetSessionDataQuery$variables = {
  sessionId: string;
};
export type AppGetSessionDataQuery$data = {
  readonly activeScenario: {
    readonly annotationId: string | null | undefined;
    readonly apps: ReadonlyArray<{
      readonly appName: string;
      readonly appTools: ReadonlyArray<{
        readonly description: string | null | undefined;
        readonly name: string;
        readonly params: ReadonlyArray<{
          readonly argType: string;
          readonly defaultValue: string | null | undefined;
          readonly description: string | null | undefined;
          readonly exampleValue: string | null | undefined;
          readonly hasDefaultValue: boolean;
          readonly name: string;
        }>;
        readonly returnDescription: string | null | undefined;
        readonly role: string;
        readonly writeOperation: boolean | null | undefined;
      }>;
    }>;
    readonly comment: string | null | undefined;
    readonly duration: number | null | undefined;
    readonly guiConfig: {
      readonly showTimestamps: boolean;
    };
    readonly scenarioId: string;
    readonly startTime: number | null | undefined;
    readonly status: string;
    readonly tags: ReadonlyArray<CapabilityTag> | null | undefined;
    readonly timeIncrementInSeconds: number | null | undefined;
  } | null | undefined;
  readonly agentConfig: any | null | undefined;
  readonly agentName: string | null | undefined;
};
export type AppGetSessionDataQuery = {
  response: AppGetSessionDataQuery$data;
  variables: AppGetSessionDataQuery$variables;
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
    "kind": "Variable",
    "name": "sessionId",
    "variableName": "sessionId"
  }
],
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v3 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "description",
  "storageKey": null
},
v4 = [
  {
    "alias": null,
    "args": (v1/*: any*/),
    "concreteType": "ScenarioForGraphQL",
    "kind": "LinkedField",
    "name": "activeScenario",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "concreteType": "ScenarioGUIConfigForGraphQL",
        "kind": "LinkedField",
        "name": "guiConfig",
        "plural": false,
        "selections": [
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "showTimestamps",
            "storageKey": null
          }
        ],
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "scenarioId",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "startTime",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "duration",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "timeIncrementInSeconds",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "status",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "comment",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "annotationId",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "tags",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "concreteType": "AppForGraphQL",
        "kind": "LinkedField",
        "name": "apps",
        "plural": true,
        "selections": [
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "appName",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "concreteType": "AppToolForGraphQL",
            "kind": "LinkedField",
            "name": "appTools",
            "plural": true,
            "selections": [
              (v2/*: any*/),
              (v3/*: any*/),
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "returnDescription",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "role",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "writeOperation",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "concreteType": "AppToolParamsForGraphQL",
                "kind": "LinkedField",
                "name": "params",
                "plural": true,
                "selections": [
                  (v2/*: any*/),
                  (v3/*: any*/),
                  {
                    "alias": null,
                    "args": null,
                    "kind": "ScalarField",
                    "name": "argType",
                    "storageKey": null
                  },
                  {
                    "alias": null,
                    "args": null,
                    "kind": "ScalarField",
                    "name": "hasDefaultValue",
                    "storageKey": null
                  },
                  {
                    "alias": null,
                    "args": null,
                    "kind": "ScalarField",
                    "name": "defaultValue",
                    "storageKey": null
                  },
                  {
                    "alias": null,
                    "args": null,
                    "kind": "ScalarField",
                    "name": "exampleValue",
                    "storageKey": null
                  }
                ],
                "storageKey": null
              }
            ],
            "storageKey": null
          }
        ],
        "storageKey": null
      }
    ],
    "storageKey": null
  },
  {
    "alias": null,
    "args": (v1/*: any*/),
    "kind": "ScalarField",
    "name": "agentName",
    "storageKey": null
  },
  {
    "alias": null,
    "args": (v1/*: any*/),
    "kind": "ScalarField",
    "name": "agentConfig",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "AppGetSessionDataQuery",
    "selections": (v4/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "AppGetSessionDataQuery",
    "selections": (v4/*: any*/)
  },
  "params": {
    "cacheID": "3621aa6acd35356f8297b3742a6a36ed",
    "id": null,
    "metadata": {},
    "name": "AppGetSessionDataQuery",
    "operationKind": "query",
    "text": "query AppGetSessionDataQuery(\n  $sessionId: String!\n) {\n  activeScenario(sessionId: $sessionId) {\n    guiConfig {\n      showTimestamps\n    }\n    scenarioId\n    startTime\n    duration\n    timeIncrementInSeconds\n    status\n    comment\n    annotationId\n    tags\n    apps {\n      appName\n      appTools {\n        name\n        description\n        returnDescription\n        role\n        writeOperation\n        params {\n          name\n          description\n          argType\n          hasDefaultValue\n          defaultValue\n          exampleValue\n        }\n      }\n    }\n  }\n  agentName(sessionId: $sessionId)\n  agentConfig(sessionId: $sessionId)\n}\n"
  }
};
})();

(node as any).hash = "e1465bd38ae50e8bc460368ae5524eea";

export default node;
