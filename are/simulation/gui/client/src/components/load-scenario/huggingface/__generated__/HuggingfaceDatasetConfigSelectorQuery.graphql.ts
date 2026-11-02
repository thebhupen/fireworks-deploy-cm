/**
 * @generated SignedSource<<9478d560e5db9dcb50bedca0a1401161>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type HuggingfaceDatasetConfigSelectorQuery$variables = {
  datasetName: string;
};
export type HuggingfaceDatasetConfigSelectorQuery$data = {
  readonly getHuggingfaceDatasetConfigs: ReadonlyArray<string>;
};
export type HuggingfaceDatasetConfigSelectorQuery = {
  response: HuggingfaceDatasetConfigSelectorQuery$data;
  variables: HuggingfaceDatasetConfigSelectorQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "datasetName"
  }
],
v1 = {
  "alias": null,
  "args": [
    {
      "kind": "Variable",
      "name": "datasetName",
      "variableName": "datasetName"
    }
  ],
  "kind": "ScalarField",
  "name": "getHuggingfaceDatasetConfigs",
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "HuggingfaceDatasetConfigSelectorQuery",
    "selections": [
      {
        "kind": "RequiredField",
        "field": (v1/*: any*/),
        "action": "THROW"
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "HuggingfaceDatasetConfigSelectorQuery",
    "selections": [
      (v1/*: any*/)
    ]
  },
  "params": {
    "cacheID": "03086d2151af1284f1cef0f7113b722d",
    "id": null,
    "metadata": {},
    "name": "HuggingfaceDatasetConfigSelectorQuery",
    "operationKind": "query",
    "text": "query HuggingfaceDatasetConfigSelectorQuery(\n  $datasetName: String!\n) {\n  getHuggingfaceDatasetConfigs(datasetName: $datasetName)\n}\n"
  }
};
})();

(node as any).hash = "be107e55c8b0f288d95c5070de827d4f";

export default node;
