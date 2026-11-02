/**
 * @generated SignedSource<<d4c5a747cc20fbbb92ebf4097e801ad5>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type FileSystemSectionGetDownloadQuery$variables = {
  filePath: string;
  filesystemAppName: string;
  sessionId: string;
};
export type FileSystemSectionGetDownloadQuery$data = {
  readonly downloadFile: string | null | undefined;
};
export type FileSystemSectionGetDownloadQuery = {
  response: FileSystemSectionGetDownloadQuery$data;
  variables: FileSystemSectionGetDownloadQuery$variables;
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
    "name": "downloadFile",
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
    "name": "FileSystemSectionGetDownloadQuery",
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
    "name": "FileSystemSectionGetDownloadQuery",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "8b2710d1c09a6f97f5d455177da25ce2",
    "id": null,
    "metadata": {},
    "name": "FileSystemSectionGetDownloadQuery",
    "operationKind": "query",
    "text": "query FileSystemSectionGetDownloadQuery(\n  $sessionId: String!\n  $filesystemAppName: String!\n  $filePath: String!\n) {\n  downloadFile(sessionId: $sessionId, filesystemAppName: $filesystemAppName, filePath: $filePath)\n}\n"
  }
};
})();

(node as any).hash = "75796de6c364fd4a684cb3fd4a72dbf1";

export default node;
