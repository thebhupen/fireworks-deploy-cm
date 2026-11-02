/**
 * @generated SignedSource<<918efbcb6585b18e5ce11b92e168aee9>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type DeleteAllScenarioEventsMutation$variables = {
  sessionId: string;
};
export type DeleteAllScenarioEventsMutation$data = {
  readonly deleteAllScenarioEvents: any | null | undefined;
};
export type DeleteAllScenarioEventsMutation = {
  response: DeleteAllScenarioEventsMutation$data;
  variables: DeleteAllScenarioEventsMutation$variables;
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
    "name": "deleteAllScenarioEvents",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "DeleteAllScenarioEventsMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "DeleteAllScenarioEventsMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "df1e9ddc734356272576be5c5a3975d6",
    "id": null,
    "metadata": {},
    "name": "DeleteAllScenarioEventsMutation",
    "operationKind": "mutation",
    "text": "mutation DeleteAllScenarioEventsMutation(\n  $sessionId: String!\n) {\n  deleteAllScenarioEvents(sessionId: $sessionId)\n}\n"
  }
};
})();

(node as any).hash = "52a4653fbfb34232464d13e948a3dd6b";

export default node;
