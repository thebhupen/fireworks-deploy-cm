/**
 * @generated SignedSource<<090bf72ffcbf8c7ffd5362f2a903ed7b>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type DeleteLogsAfterMutation$variables = {
  edit?: string | null | undefined;
  id: string;
  sessionId: string;
};
export type DeleteLogsAfterMutation$data = {
  readonly deleteLogsAfter: {
    readonly scenarioId: string;
  } | null | undefined;
};
export type DeleteLogsAfterMutation = {
  response: DeleteLogsAfterMutation$data;
  variables: DeleteLogsAfterMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "edit"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "id"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v3 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "edit",
        "variableName": "edit"
      },
      {
        "kind": "Variable",
        "name": "id",
        "variableName": "id"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "concreteType": "ScenarioForGraphQL",
    "kind": "LinkedField",
    "name": "deleteLogsAfter",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "scenarioId",
        "storageKey": null
      }
    ],
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "DeleteLogsAfterMutation",
    "selections": (v3/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v2/*: any*/),
      (v1/*: any*/),
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "DeleteLogsAfterMutation",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "8ccb5ab42d539d536b8f33d0f6140512",
    "id": null,
    "metadata": {},
    "name": "DeleteLogsAfterMutation",
    "operationKind": "mutation",
    "text": "mutation DeleteLogsAfterMutation(\n  $sessionId: String!\n  $id: String!\n  $edit: String\n) {\n  deleteLogsAfter(sessionId: $sessionId, id: $id, edit: $edit) {\n    scenarioId\n  }\n}\n"
  }
};
})();

(node as any).hash = "ead3ad118305ed1d55b8f3a5e903285e";

export default node;
