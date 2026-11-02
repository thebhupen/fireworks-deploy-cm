/**
 * @generated SignedSource<<553182ddeb55e2a16321e2cf0837c0e3>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type EditTimeIncrementMutation$variables = {
  sessionId: string;
  timeIncrement: number;
};
export type EditTimeIncrementMutation$data = {
  readonly editTimeIncrement: number;
};
export type EditTimeIncrementMutation = {
  response: EditTimeIncrementMutation$data;
  variables: EditTimeIncrementMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "sessionId"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "timeIncrement"
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
      },
      {
        "kind": "Variable",
        "name": "timeIncrementInSeconds",
        "variableName": "timeIncrement"
      }
    ],
    "kind": "ScalarField",
    "name": "editTimeIncrement",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "EditTimeIncrementMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "EditTimeIncrementMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "a4fbf28fe246d973781033825b5f391e",
    "id": null,
    "metadata": {},
    "name": "EditTimeIncrementMutation",
    "operationKind": "mutation",
    "text": "mutation EditTimeIncrementMutation(\n  $sessionId: String!\n  $timeIncrement: Int!\n) {\n  editTimeIncrement(sessionId: $sessionId, timeIncrementInSeconds: $timeIncrement)\n}\n"
  }
};
})();

(node as any).hash = "a6a0f2c754777160146601ed34059c54";

export default node;
