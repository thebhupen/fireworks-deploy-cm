/**
 * @generated SignedSource<<7875eaaea1ef7a46ec6536f3ec69ccae>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type FileUploadDialogUploadFileMutation$variables = {
  destinationPath: string;
  fileContent: string;
  fileName: string;
  filesystemAppName: string;
  sessionId: string;
};
export type FileUploadDialogUploadFileMutation$data = {
  readonly uploadFile: boolean;
};
export type FileUploadDialogUploadFileMutation = {
  response: FileUploadDialogUploadFileMutation$data;
  variables: FileUploadDialogUploadFileMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "destinationPath"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "fileContent"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "fileName"
},
v3 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "filesystemAppName"
},
v4 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "sessionId"
},
v5 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "destinationPath",
        "variableName": "destinationPath"
      },
      {
        "kind": "Variable",
        "name": "fileContent",
        "variableName": "fileContent"
      },
      {
        "kind": "Variable",
        "name": "fileName",
        "variableName": "fileName"
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
    "name": "uploadFile",
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/),
      (v4/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "FileUploadDialogUploadFileMutation",
    "selections": (v5/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v4/*: any*/),
      (v3/*: any*/),
      (v2/*: any*/),
      (v1/*: any*/),
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "FileUploadDialogUploadFileMutation",
    "selections": (v5/*: any*/)
  },
  "params": {
    "cacheID": "6cb20d79ba2d720fd90573704a8267cc",
    "id": null,
    "metadata": {},
    "name": "FileUploadDialogUploadFileMutation",
    "operationKind": "mutation",
    "text": "mutation FileUploadDialogUploadFileMutation(\n  $sessionId: String!\n  $filesystemAppName: String!\n  $fileName: String!\n  $fileContent: String!\n  $destinationPath: String!\n) {\n  uploadFile(sessionId: $sessionId, filesystemAppName: $filesystemAppName, fileName: $fileName, fileContent: $fileContent, destinationPath: $destinationPath)\n}\n"
  }
};
})();

(node as any).hash = "20717f24a9b3f3df98133d3a787d9718";

export default node;
