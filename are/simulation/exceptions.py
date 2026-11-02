# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


class LoggedError(Exception):
    """
    Base class for agent exceptions that should be logged.
    """

    category = "LoggedError"

    def __init__(self, message: str | None = ""):
        super().__init__(message)
        self.message = message


class FatalError(LoggedError):
    """
    Base class for fatal errors that lead to task failure.
    """

    category = "FatalError"


class FormatError(LoggedError):
    """
    Base class for agent exceptions that should be logged.
    """

    category = "FormatError"


class ServerError(LoggedError):
    """
    Base class for server errors.
    """

    category = "ServerError"


class AgentError(LoggedError):
    """
    Base class for agent errors.
    """

    category = "AgentError"


class ToolError(LoggedError):
    """
    Base class for tool errors.
    """

    category = "ToolError"


class WebError(LoggedError):
    """
    Base class for web browsing errors.
    """

    category = "WebError"


class MarkdownConverterError(LoggedError):
    """
    Base class for MarkdownConverter errors.
    """

    category = "MarkdownConverterError"


class InvalidActionAgentError(AgentError):
    """
    The agent wrote a malformed output, e.g. missing 'Thought:' or 'Action:'
    """


class JsonParsingAgentError(AgentError):
    """
    The JSON agent called a tool with an inappropriate JSON format.
    """


class JsonExecutionAgentError(AgentError):
    """
    The JSON agent called a tool that failed to execute.
    """


class UnavailableToolAgentError(AgentError):
    """
    The agent called a tool that is not available.
    """


class MaxIterationsAgentError(AgentError):
    """
    The agent reached the maximum number of iterations without completing the task.
    """


class TimeoutAgentError(AgentError):
    """
    The agent reached the timeout without completing the task.
    """


class InvalidToolCallError(ToolError):
    """
    The agent called a tool with an invalid argument.
    """


class NoSearchResultsWebError(WebError):
    """
    The agent successfully called the search API (Bing/Google), but the search failed because:
    - The API found no relevant results for the query
    - No direct link could be found in the search results
    """


class SearchApiConnectionWebError(WebError):
    """
    The agent called the search API (Bing/Google), but the search failed because:
    - The API could not be reached (e.g. HTTPError)
    - The API returned an error response (e.g. RateLimitExceeded)
    """


class InfoSearchWebError(WebError):
    """
    The agent called the 'web_search' tool but the search failed to return any results.
    """


class VisitPageWebError(WebError):
    """
    The agent called the 'visit_page' tool but the page could not be loaded.
    """
