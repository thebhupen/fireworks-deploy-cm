/**
 * @generated SignedSource<<3db6f81dc019ea65260f396b49951b0b>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type AgentLogTypeForGraphQL = "AGENT_STOP" | "CODE_EXECUTION_RESULT" | "CODE_STATE_UPDATE" | "END_TASK" | "ERROR" | "FACTS" | "FINAL_ANSWER" | "LLM_INPUT" | "LLM_OUTPUT_FACTS" | "LLM_OUTPUT_PLAN" | "LLM_OUTPUT_THOUGHT_ACTION" | "LOG" | "OBSERVATION" | "PLAN" | "RATIONALE" | "REFACTS" | "REPLAN" | "STEP" | "SUBAGENT" | "SYSTEM_PROMPT" | "TASK" | "THOUGHT" | "TOOL_CALL" | "%future added value";
export type EnvironmentState = "FAILED" | "PAUSED" | "RUNNING" | "SETUP" | "STOPPED" | "%future added value";
export type HintType = "ENVIRONMENT_HINT" | "TASK_HINT" | "%future added value";
export type AppEnvironmentSubscription$variables = {
  sessionId: string;
};
export type AppEnvironmentSubscription$data = {
  readonly environmentSubscriptionState: {
    readonly appsStateJson: string | null | undefined;
    readonly envState: EnvironmentState | null | undefined;
    readonly environmentTime: number | null | undefined;
    readonly eventLogJson: string | null | undefined;
    readonly hints: ReadonlyArray<{
      readonly associatedEventId: string;
      readonly content: string;
      readonly hintType: HintType;
    }> | null | undefined;
    readonly initialEventQueueJson: string | null | undefined;
    readonly worldLogs: ReadonlyArray<{
      readonly actionName: string | null | undefined;
      readonly appName: string | null | undefined;
      readonly attachments: ReadonlyArray<{
        readonly length: number;
        readonly mime: string;
        readonly url: string;
      }> | null | undefined;
      readonly content: string | null | undefined;
      readonly exception: string | null | undefined;
      readonly exceptionStackTrace: string | null | undefined;
      readonly groupId: string | null | undefined;
      readonly id: string;
      readonly input: string | null | undefined;
      readonly isSubagent: boolean;
      readonly output: string | null | undefined;
      readonly startId: string | null | undefined;
      readonly timestamp: number | null | undefined;
      readonly type: AgentLogTypeForGraphQL;
    }> | null | undefined;
  };
};
export type AppEnvironmentSubscription = {
  response: AppEnvironmentSubscription$data;
  variables: AppEnvironmentSubscription$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "sessionId"
  }
],
v1 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "content",
  "storageKey": null
},
v2 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "sessionId",
        "variableName": "sessionId"
      }
    ],
    "concreteType": "EnvironmentSubscriptionState",
    "kind": "LinkedField",
    "name": "environmentSubscriptionState",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "appsStateJson",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "eventLogJson",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "initialEventQueueJson",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "envState",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "environmentTime",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "concreteType": "AgentLogForGraphQL",
        "kind": "LinkedField",
        "name": "worldLogs",
        "plural": true,
        "selections": [
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "id",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "groupId",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "type",
            "storageKey": null
          },
          (v1/*: any*/),
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "startId",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "timestamp",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "input",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "actionName",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "appName",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "output",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "exception",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "exceptionStackTrace",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "concreteType": "AttachmentForGraphQL",
            "kind": "LinkedField",
            "name": "attachments",
            "plural": true,
            "selections": [
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "length",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "mime",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "url",
                "storageKey": null
              }
            ],
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "isSubagent",
            "storageKey": null
          }
        ],
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "concreteType": "Hint",
        "kind": "LinkedField",
        "name": "hints",
        "plural": true,
        "selections": [
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "hintType",
            "storageKey": null
          },
          (v1/*: any*/),
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "associatedEventId",
            "storageKey": null
          }
        ],
        "storageKey": null
      }
    ],
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "AppEnvironmentSubscription",
    "selections": (v2/*: any*/),
    "type": "Subscription",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "AppEnvironmentSubscription",
    "selections": (v2/*: any*/)
  },
  "params": {
    "cacheID": "5f9cac62bb110a718a0095344def26eb",
    "id": null,
    "metadata": {},
    "name": "AppEnvironmentSubscription",
    "operationKind": "subscription",
    "text": "subscription AppEnvironmentSubscription(\n  $sessionId: String!\n) {\n  environmentSubscriptionState(sessionId: $sessionId) {\n    appsStateJson\n    eventLogJson\n    initialEventQueueJson\n    envState\n    environmentTime\n    worldLogs {\n      id\n      groupId\n      type\n      content\n      startId\n      timestamp\n      input\n      actionName\n      appName\n      output\n      exception\n      exceptionStackTrace\n      attachments {\n        length\n        mime\n        url\n      }\n      isSubagent\n    }\n    hints {\n      hintType\n      content\n      associatedEventId\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "de4d7768f297b1106ff568b9b4d84dcb";

export default node;
