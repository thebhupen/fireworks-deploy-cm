/**
 * @generated SignedSource<<ce973b62a8d673fb1d17e528bb99249a>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type AppGetStaticDataQuery$variables = Record<PropertyKey, never>;
export type AppGetStaticDataQuery$data = {
  readonly allAgents: ReadonlyArray<string>;
  readonly allScenarios: ReadonlyArray<string>;
  readonly defaultUiView: string | null | undefined;
};
export type AppGetStaticDataQuery = {
  response: AppGetStaticDataQuery$data;
  variables: AppGetStaticDataQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "allScenarios",
    "storageKey": null
  },
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "allAgents",
    "storageKey": null
  },
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "defaultUiView",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "AppGetStaticDataQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "AppGetStaticDataQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "a83c6f1ac97496768f5558f320059a72",
    "id": null,
    "metadata": {},
    "name": "AppGetStaticDataQuery",
    "operationKind": "query",
    "text": "query AppGetStaticDataQuery {\n  allScenarios\n  allAgents\n  defaultUiView\n}\n"
  }
};
})();

(node as any).hash = "fde3be6b7c31e033d92a0135447cf4c4";

export default node;
