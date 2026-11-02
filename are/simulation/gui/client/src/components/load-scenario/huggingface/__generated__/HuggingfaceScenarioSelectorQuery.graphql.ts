/**
 * @generated SignedSource<<3a88679f617a59314c9e78fbc2179c41>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type HuggingfaceScenarioSelectorQuery$variables = {
  datasetConfig: string;
  datasetName: string;
  datasetSplit: string;
};
export type HuggingfaceScenarioSelectorQuery$data = {
  readonly getHuggingfaceScenarios: ReadonlyArray<string>;
};
export type HuggingfaceScenarioSelectorQuery = {
  response: HuggingfaceScenarioSelectorQuery$data;
  variables: HuggingfaceScenarioSelectorQuery$variables;
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
    }
  ],
  "kind": "ScalarField",
  "name": "getHuggingfaceScenarios",
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "HuggingfaceScenarioSelectorQuery",
    "selections": [
      {
        "kind": "RequiredField",
        "field": (v3/*: any*/),
        "action": "THROW"
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v1/*: any*/),
      (v0/*: any*/),
      (v2/*: any*/)
    ],
    "kind": "Operation",
    "name": "HuggingfaceScenarioSelectorQuery",
    "selections": [
      (v3/*: any*/)
    ]
  },
  "params": {
    "cacheID": "99fa05d44ba84219a83060c217896880",
    "id": null,
    "metadata": {},
    "name": "HuggingfaceScenarioSelectorQuery",
    "operationKind": "query",
    "text": "query HuggingfaceScenarioSelectorQuery(\n  $datasetName: String!\n  $datasetConfig: String!\n  $datasetSplit: String!\n) {\n  getHuggingfaceScenarios(datasetName: $datasetName, datasetConfig: $datasetConfig, datasetSplit: $datasetSplit)\n}\n"
  }
};
})();

(node as any).hash = "ba54bd11976dffaac4326e473139dace";

export default node;
