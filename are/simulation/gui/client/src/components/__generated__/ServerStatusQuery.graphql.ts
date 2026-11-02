/**
 * @generated SignedSource<<e763eaf0d9dd1b4789f01ef42fa01909>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type ServerStatusQuery$variables = Record<PropertyKey, never>;
export type ServerStatusQuery$data = {
  readonly serverInfo: {
    readonly serverId: string;
    readonly serverVersion: string;
  };
};
export type ServerStatusQuery = {
  response: ServerStatusQuery$data;
  variables: ServerStatusQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "concreteType": "ServerInfoForGraphQL",
    "kind": "LinkedField",
    "name": "serverInfo",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "serverId",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "serverVersion",
        "storageKey": null
      }
    ],
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "ServerStatusQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "ServerStatusQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "8a9a0cba0261868327d8e5f43df39c36",
    "id": null,
    "metadata": {},
    "name": "ServerStatusQuery",
    "operationKind": "query",
    "text": "query ServerStatusQuery {\n  serverInfo {\n    serverId\n    serverVersion\n  }\n}\n"
  }
};
})();

(node as any).hash = "96807ab8efb0e71900fa328d4833f8fa";

export default node;
