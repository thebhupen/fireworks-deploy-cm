/**
 * @generated SignedSource<<a977c6982dc11da23e8984a08cbaf2fa>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type InitConnectWithSessionIdMutation$variables = {
  sessionId: string;
};
export type InitConnectWithSessionIdMutation$data = {
  readonly initConnectWithSessionId: string;
};
export type InitConnectWithSessionIdMutation = {
  response: InitConnectWithSessionIdMutation$data;
  variables: InitConnectWithSessionIdMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "sessionId"
  }
],
v1 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "initConnectWithSessionId",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "InitConnectWithSessionIdMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "InitConnectWithSessionIdMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "605d47eabad61e1fa5c3a8fa16440384",
    "id": null,
    "metadata": {},
    "name": "InitConnectWithSessionIdMutation",
    "operationKind": "mutation",
    "text": "mutation InitConnectWithSessionIdMutation(\n  $sessionId: String!\n) {\n  initConnectWithSessionId(sessionId: $sessionId)\n}\n"
  }
};
})();

(node as any).hash = "cb89e2a67d6e8dd41efcf96020b7accc";

export default node;
