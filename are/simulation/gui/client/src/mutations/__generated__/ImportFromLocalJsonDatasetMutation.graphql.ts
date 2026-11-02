/**
 * @generated SignedSource<<7f30efd106dd32f758de40921f4e39e6>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type CapabilityTag = "Adaptability" | "Ambiguity" | "Collaboration" | "Execution" | "Exploration" | "Memory" | "Planning" | "PromptInjection" | "Safety" | "Search" | "Security" | "Time" | "UnitTest" | "Universe" | "%future added value";
export type ImportFromLocalJsonDatasetMutation$variables = {
  capability: string;
  filename: string;
  replayLogs: boolean;
  sessionId: string;
};
export type ImportFromLocalJsonDatasetMutation$data = {
  readonly importFromLocalJsonDataset: {
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
export type ImportFromLocalJsonDatasetMutation = {
  response: ImportFromLocalJsonDatasetMutation$data;
  variables: ImportFromLocalJsonDatasetMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "capability"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "filename"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "replayLogs"
},
v3 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v4 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v5 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "description",
  "storageKey": null
},
v6 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "capability",
        "variableName": "capability"
      },
      {
        "kind": "Variable",
        "name": "filename",
        "variableName": "filename"
      },
      {
        "kind": "Variable",
        "name": "replayLogs",
        "variableName": "replayLogs"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "concreteType": "ScenarioForGraphQL",
    "kind": "LinkedField",
    "name": "importFromLocalJsonDataset",
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
              (v4/*: any*/),
              (v5/*: any*/),
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
                  (v4/*: any*/),
                  (v5/*: any*/),
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
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "ImportFromLocalJsonDatasetMutation",
    "selections": (v6/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v3/*: any*/),
      (v2/*: any*/)
    ],
    "kind": "Operation",
    "name": "ImportFromLocalJsonDatasetMutation",
    "selections": (v6/*: any*/)
  },
  "params": {
    "cacheID": "a91f9fe1830f6724e17e8ddb31661e40",
    "id": null,
    "metadata": {},
    "name": "ImportFromLocalJsonDatasetMutation",
    "operationKind": "mutation",
    "text": "mutation ImportFromLocalJsonDatasetMutation(\n  $capability: String!\n  $filename: String!\n  $sessionId: String!\n  $replayLogs: Boolean!\n) {\n  importFromLocalJsonDataset(capability: $capability, filename: $filename, sessionId: $sessionId, replayLogs: $replayLogs) {\n    guiConfig {\n      showTimestamps\n    }\n    scenarioId\n    startTime\n    duration\n    timeIncrementInSeconds\n    status\n    comment\n    annotationId\n    tags\n    apps {\n      appName\n      appTools {\n        name\n        description\n        returnDescription\n        role\n        writeOperation\n        params {\n          name\n          description\n          argType\n          hasDefaultValue\n          defaultValue\n          exampleValue\n        }\n      }\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "416847ea076a89869cd6ab80932e0fb5";

export default node;
