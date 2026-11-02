/**
 * @generated SignedSource<<c5e51d8481c2f7a8db91a4308ec710b2>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type useDefaultScenarioIdQuery$variables = Record<PropertyKey, never>;
export type useDefaultScenarioIdQuery$data = {
  readonly getDefaultScenarioId: string | null | undefined;
};
export type useDefaultScenarioIdQuery = {
  response: useDefaultScenarioIdQuery$data;
  variables: useDefaultScenarioIdQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "getDefaultScenarioId",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "useDefaultScenarioIdQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "useDefaultScenarioIdQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "db5a7f459fc1c7671ceebb16e0108fc0",
    "id": null,
    "metadata": {},
    "name": "useDefaultScenarioIdQuery",
    "operationKind": "query",
    "text": "query useDefaultScenarioIdQuery {\n  getDefaultScenarioId\n}\n"
  }
};
})();

(node as any).hash = "b71acc0f35234793d95e761938a0f91a";

export default node;
