/**
 * @generated SignedSource<<fcce4b056eab3656f74c3c7ff060a291>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type FileSystemImageLoaderGetFileContentQuery$variables = {
  filePath: string;
  filesystemAppName: string;
  sessionId: string;
};
export type FileSystemImageLoaderGetFileContentQuery$data = {
  readonly getFileContent: string | null | undefined;
};
export type FileSystemImageLoaderGetFileContentQuery = {
  response: FileSystemImageLoaderGetFileContentQuery$data;
  variables: FileSystemImageLoaderGetFileContentQuery$variables;
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
    "name": "FileSystemImageLoaderGetFileContentQuery",
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
    "name": "FileSystemImageLoaderGetFileContentQuery",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "49361f020b610f8c745617056beff996",
    "id": null,
    "metadata": {},
    "name": "FileSystemImageLoaderGetFileContentQuery",
    "operationKind": "query",
    "text": "query FileSystemImageLoaderGetFileContentQuery(\n  $sessionId: String!\n  $filesystemAppName: String!\n  $filePath: String!\n) {\n  getFileContent(sessionId: $sessionId, filesystemAppName: $filesystemAppName, filePath: $filePath)\n}\n"
  }
};
})();

(node as any).hash = "8ae7daae404f79e5c0cfe865124f3300";

export default node;
