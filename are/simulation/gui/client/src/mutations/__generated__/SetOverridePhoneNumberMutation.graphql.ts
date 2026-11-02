/**
 * @generated SignedSource<<ec8110dfac61ec2292c3ce111eaace1e>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type SetOverridePhoneNumberMutation$variables = {
  overridePhoneNumber?: string | null | undefined;
  sessionId: string;
};
export type SetOverridePhoneNumberMutation$data = {
  readonly setOverridePhoneNumber: string | null | undefined;
};
export type SetOverridePhoneNumberMutation = {
  response: SetOverridePhoneNumberMutation$data;
  variables: SetOverridePhoneNumberMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "overridePhoneNumber"
  },
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
        "name": "overridePhoneNumber",
        "variableName": "overridePhoneNumber"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "setOverridePhoneNumber",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "SetOverridePhoneNumberMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "SetOverridePhoneNumberMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "d172d61f81c1f2d51c0704c79179a94c",
    "id": null,
    "metadata": {},
    "name": "SetOverridePhoneNumberMutation",
    "operationKind": "mutation",
    "text": "mutation SetOverridePhoneNumberMutation(\n  $overridePhoneNumber: String\n  $sessionId: String!\n) {\n  setOverridePhoneNumber(overridePhoneNumber: $overridePhoneNumber, sessionId: $sessionId)\n}\n"
  }
};
})();

(node as any).hash = "cc30e9015980120269b5b7094f50667b";

export default node;
