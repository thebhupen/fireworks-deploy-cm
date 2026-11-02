/**
 * @generated SignedSource<<32e5ed481b1cd85d23345cd8117a266f>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type HuggingfaceDatasetSplitSelectorQuery$variables = {
  datasetConfig: string;
  datasetName: string;
};
export type HuggingfaceDatasetSplitSelectorQuery$data = {
  readonly getHuggingfaceDatasetSplits: ReadonlyArray<string>;
};
export type HuggingfaceDatasetSplitSelectorQuery = {
  response: HuggingfaceDatasetSplitSelectorQuery$data;
  variables: HuggingfaceDatasetSplitSelectorQuery$variables;
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
    }
  ],
  "kind": "ScalarField",
  "name": "getHuggingfaceDatasetSplits",
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "HuggingfaceDatasetSplitSelectorQuery",
    "selections": [
      {
        "kind": "RequiredField",
        "field": (v2/*: any*/),
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
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "HuggingfaceDatasetSplitSelectorQuery",
    "selections": [
      (v2/*: any*/)
    ]
  },
  "params": {
    "cacheID": "25d77247e86a35265addb23e9d7835c7",
    "id": null,
    "metadata": {},
    "name": "HuggingfaceDatasetSplitSelectorQuery",
    "operationKind": "query",
    "text": "query HuggingfaceDatasetSplitSelectorQuery(\n  $datasetName: String!\n  $datasetConfig: String!\n) {\n  getHuggingfaceDatasetSplits(datasetName: $datasetName, datasetConfig: $datasetConfig)\n}\n"
  }
};
})();

(node as any).hash = "f4bb8fb769ec9ac2665ebce0da68dd6f";

export default node;
