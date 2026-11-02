/**
 * @generated SignedSource<<897876a4f88c721fa79fa00353dc4cae>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type FileSystemSectionGetFileContentQuery$variables = {
  filePath: string;
  filesystemAppName: string;
  sessionId: string;
};
export type FileSystemSectionGetFileContentQuery$data = {
  readonly getFileContent: string | null | undefined;
};
export type FileSystemSectionGetFileContentQuery = {
  response: FileSystemSectionGetFileContentQuery$data;
  variables: FileSystemSectionGetFileContentQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "filePath"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "filesystemAppName"
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
        "name": "filePath",
        "variableName": "filePath"
      },
      {
        "kind": "Variable",
        "name": "filesystemAppName",
        "variableName": "filesystemAppName"
      },
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "kind": "ScalarField",
    "name": "getFileContent",
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
    "name": "FileSystemSectionGetFileContentQuery",
    "selections": (v3/*: any*/),
    "type": "Query",
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
    "name": "FileSystemSectionGetFileContentQuery",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "be5bc876b9cb9b4e424e536a454ab582",
    "id": null,
    "metadata": {},
    "name": "FileSystemSectionGetFileContentQuery",
    "operationKind": "query",
    "text": "query FileSystemSectionGetFileContentQuery(\n  $sessionId: String!\n  $filesystemAppName: String!\n  $filePath: String!\n) {\n  getFileContent(sessionId: $sessionId, filesystemAppName: $filesystemAppName, filePath: $filePath)\n}\n"
  }
};
})();

(node as any).hash = "f0492938dc149fba8d5c9912a33b4c2e";

export default node;
