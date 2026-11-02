/**
 * @generated SignedSource<<dddb3cf63afb0ecd5114b1096d8841c7>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type SetUserNameMutation$variables = {
  name?: string | null | undefined;
  sessionId: string;
};
export type SetUserNameMutation$data = {
  readonly setAnnotatorName: string | null | undefined;
};
export type SetUserNameMutation = {
  response: SetUserNameMutation$data;
  variables: SetUserNameMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "name"
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
        "name": "name",
        "variableName": "name"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "setAnnotatorName",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "SetUserNameMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "SetUserNameMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "a2337d1e0f7910e4132e960857532ee3",
    "id": null,
    "metadata": {},
    "name": "SetUserNameMutation",
    "operationKind": "mutation",
    "text": "mutation SetUserNameMutation(\n  $name: String\n  $sessionId: String!\n) {\n  setAnnotatorName(name: $name, sessionId: $sessionId)\n}\n"
  }
};
})();

(node as any).hash = "358fa898e0efb7203842484ff753cafd";

export default node;
