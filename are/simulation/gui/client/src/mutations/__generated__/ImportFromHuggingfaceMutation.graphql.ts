/**
 * @generated SignedSource<<ea366d2c417b5e0ca4940520e127792c>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type CapabilityTag = "Adaptability" | "Ambiguity" | "Collaboration" | "Execution" | "Exploration" | "Memory" | "Planning" | "PromptInjection" | "Safety" | "Search" | "Security" | "Time" | "UnitTest" | "Universe" | "%future added value";
export type ImportFromHuggingfaceMutation$variables = {
  datasetConfig: string;
  datasetName: string;
  datasetSplit: string;
  scenarioId: string;
  sessionId: string;
};
export type ImportFromHuggingfaceMutation$data = {
  readonly importFromHuggingface: {
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
export type ImportFromHuggingfaceMutation = {
  response: ImportFromHuggingfaceMutation$data;
  variables: ImportFromHuggingfaceMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "datasetConfig"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "datasetName"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "datasetSplit"
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
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v6 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "description",
  "storageKey": null
},
v7 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "datasetConfig",
        "variableName": "datasetConfig"
      },
      {
        "kind": "Variable",
        "name": "datasetName",
        "variableName": "datasetName"
      },
      {
        "kind": "Variable",
        "name": "datasetSplit",
        "variableName": "datasetSplit"
      },
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
    "name": "importFromHuggingface",
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
              (v5/*: any*/),
              (v6/*: any*/),
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
                  (v5/*: any*/),
                  (v6/*: any*/),
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
      (v3/*: any*/),
      (v4/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "ImportFromHuggingfaceMutation",
    "selections": (v7/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v1/*: any*/),
      (v0/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/),
      (v4/*: any*/)
    ],
    "kind": "Operation",
    "name": "ImportFromHuggingfaceMutation",
    "selections": (v7/*: any*/)
  },
  "params": {
    "cacheID": "16b76c9cf5bc4e398cba5cf880404e71",
    "id": null,
    "metadata": {},
    "name": "ImportFromHuggingfaceMutation",
    "operationKind": "mutation",
    "text": "mutation ImportFromHuggingfaceMutation(\n  $datasetName: String!\n  $datasetConfig: String!\n  $datasetSplit: String!\n  $scenarioId: String!\n  $sessionId: String!\n) {\n  importFromHuggingface(datasetName: $datasetName, datasetConfig: $datasetConfig, datasetSplit: $datasetSplit, scenarioId: $scenarioId, sessionId: $sessionId) {\n    guiConfig {\n      showTimestamps\n    }\n    scenarioId\n    startTime\n    duration\n    timeIncrementInSeconds\n    status\n    comment\n    annotationId\n    tags\n    apps {\n      appName\n      appTools {\n        name\n        description\n        returnDescription\n        role\n        writeOperation\n        params {\n          name\n          description\n          argType\n          hasDefaultValue\n          defaultValue\n          exampleValue\n        }\n      }\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "a206d35d2dcdea526d53bcf10c1eac82";

export default node;
