/**
 * @generated SignedSource<<c4354d7d2d334836638d4b092a787265>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type useInteractiveScenarioQuery$variables = Record<PropertyKey, never>;
export type useInteractiveScenarioQuery$data = {
  readonly getInteractiveScenariosTree: any | null | undefined;
};
export type useInteractiveScenarioQuery = {
  response: useInteractiveScenarioQuery$data;
  variables: useInteractiveScenarioQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "getInteractiveScenariosTree",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "useInteractiveScenarioQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "useInteractiveScenarioQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "f0facc65db8a78d4a2bed61035888898",
    "id": null,
    "metadata": {},
    "name": "useInteractiveScenarioQuery",
    "operationKind": "query",
    "text": "query useInteractiveScenarioQuery {\n  getInteractiveScenariosTree\n}\n"
  }
};
})();

(node as any).hash = "84c7e75b32cef0a5be823adaa1a52990";

export default node;
