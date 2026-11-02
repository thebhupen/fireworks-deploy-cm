/**
 * @generated SignedSource<<f5a1781aead6d4c57d3f364bf8c0ca1a>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type CapabilityTag = "Adaptability" | "Ambiguity" | "Collaboration" | "Execution" | "Exploration" | "Memory" | "Planning" | "PromptInjection" | "Safety" | "Search" | "Security" | "Time" | "UnitTest" | "Universe" | "%future added value";
export type SetScenarioMutation$variables = {
  scenarioId: string;
  sessionId: string;
};
export type SetScenarioMutation$data = {
  readonly setScenario: {
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
};
export type SetScenarioMutation = {
  response: SetScenarioMutation$data;
  variables: SetScenarioMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "scenarioId"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "sessionId"
  }
],
v1 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "description",
  "storageKey": null
},
v3 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "scenarioId",
        "variableName": "scenarioId"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "concreteType": "ScenarioForGraphQL",
    "kind": "LinkedField",
    "name": "setScenario",
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
              (v1/*: any*/),
              (v2/*: any*/),
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
                  (v1/*: any*/),
                  (v2/*: any*/),
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
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "SetScenarioMutation",
    "selections": (v3/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "SetScenarioMutation",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "2d293d27b726aaa5191c6d2b20bac20b",
    "id": null,
    "metadata": {},
    "name": "SetScenarioMutation",
    "operationKind": "mutation",
    "text": "mutation SetScenarioMutation(\n  $scenarioId: String!\n  $sessionId: String!\n) {\n  setScenario(scenarioId: $scenarioId, sessionId: $sessionId) {\n    guiConfig {\n      showTimestamps\n    }\n    scenarioId\n    startTime\n    duration\n    timeIncrementInSeconds\n    status\n    comment\n    annotationId\n    tags\n    apps {\n      appName\n      appTools {\n        name\n        description\n        returnDescription\n        role\n        writeOperation\n        params {\n          name\n          description\n          argType\n          hasDefaultValue\n          defaultValue\n          exampleValue\n        }\n      }\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "89e1728d1e6d3e934804b0ff8f6ef878";

export default node;
