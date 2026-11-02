# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import textwrap
from dataclasses import dataclass
from typing import Any

from are.simulation.validation.examples import (
    CAB_CHECKER_EXAMPLES,
    EMAIL_CHECKER_EXAMPLES,
    EVENT_CHECKER_EXAMPLES,
    EVENT_SUBTASK_EXTRACTOR_EXAMPLES,
    SIGNATURE_CHECKER_EXAMPLES,
    USER_MESSAGE_CHECKER_EXAMPLES,
    USER_MESSAGE_SUBTASK_EXTRACTOR_EXAMPLES,
)

IN_CONTEXT_JUDGE_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### Evaluator Task
    You are an impartial evaluator responsible for assessing the success of an agent assisting a user within an environment in comparison to an oracle agent.
    In this environment, the user communicates with the agent via a UserAgentInterface, and the agent utilizes tools from various apps to fulfill user requests.
    You will receive two lists of actions (each action is a tool call): one representing actions taken by the agent and another representing actions performed by a skilled oracle agent that perfectly fulfilled the user's request.

    ###Instructions
    First, you will list the differences and similarities between the actions taken by the agent and those performed by the oracle agent.
    Then, based on the evaluation criteria below, you will decide if the agent's actions match the oracle agent's actions within acceptable tolerance limits.

    ### Evaluation Criteria
    The agent's actions should be executed in an order that does not violate the causal relationships between oracle actions provided by with the parent tool call ids.
    The number of calls to each tool should be the same for the agent and the oracle agent actions.
    The agent's action call parameters should be free of significant grammatical or spelling errors and maintain an appropriate tone.
    {{evaluation_criteria}}

    ### Input Format
    The input will be provided in the following format:

    Agent Actions:

    < List of agent actions in the format:
        Tool name: <name of the tool used in the action>
        Tool call time: <time of the action>
        Arguments:
        <tool arguments>
    >

    Oracle Actions:

    < List of oracle actions in the format:
        Tool call id: <id of the oracle tool call>
        Parent tool call ids: <ids of the parent tool calls>
        Tool name: <name of the tool used in the action>
        Tool call time: <time of the action>
        Arguments:
        <tool arguments>
    >

    Task: <user's task>

    Previous task: <previous task solved by the agent>

    User name: <name of the user>

    ### Output Format
    For the evaluation, first list the differences and similarities between the agent and oracle agent actions.
    Then give your reasoning as to why the agent's actions match or critically differ from the oracle agent actions.
    Finally, provide your final evaluation by strictly following this format: "[[success]]" if the agent actions match the oracle agent actions otherwise "[[failure]]".
    Report your evaluation in the following format:

    -Similarities and differences: <List the differences and similarities between the agent and oracle agent actions.>
    -Reasoning: <Detailed explanation of why the agent's actions match or not the oracle agent actions.>
    -Evaluation: <[[success]] if the agent actions match oracle agent actions [[failure]] otherwise.>

    ### Your Evaluation
    For the following input, provide your evaluation following the output format specified above.
    """
)


TIME_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """
    All agent actions matching an oracle action with a delay exceeding {{check_time_threshold_seconds}} seconds relative to its parent should be executed within the following time window:
    [oracle action delay - {{pre_event_tolerance_seconds}} seconds, oracle action delay + {{post_event_tolerance_seconds}} seconds]
    """
)

PER_TOOL_EVALUATION_CRITERIA = {
    "CalendarApp__add_calendar_event": textwrap.dedent(
        """\
        4. The title, description and tag of the calendar event CAN BE DIFFERENT to the oracle's calendar event, UNLESS the task, if specified, asks for a specific title, description or tag.
        5. Stylistic and tone differences between the agent and oracle title and descriptions are acceptable.
        """
    ),
    "EmailClientApp__reply_to_email": textwrap.dedent(
        """\
        4. The content of the agent's email should include all information present in the oracle's email, though stylistic and tone differences are acceptable.
        5. The agent's email can provide additional context or details as long as it does not contradict the oracle's information.
        6. The agent can miss some information in content that is NOT RELEVANT for the task if specified.
        7. IMPORTANT: The agent's email should not include a signature placeholder, such as '[Your Name]', or '[User's Name]', nor placeholders for recipient names.
        8. IMPORTANT: The agent email's signature should not be 'User', 'Assistant' or 'Your assistant'.
        9. Greetings and salutations can differ between the agent and oracle emails, including the option for either party to omit them altogether.
        """
    ),
    "EmailClientApp__send_email": textwrap.dedent(
        """\
        4. The subject and the content of the agent's email should include all information present in the oracle's email, though stylistic and tone differences are acceptable.
        5. The agent's email can provide additional context or details as long as it does not contradict the oracle's information.
        6.The agent can miss some information in content that are NOT RELEVANT for the task if specified.
        7. IMPORTANT: The email should not include a signature placeholder, such as '[Your Name]', '[My Name]', or '[User's Name]', nor placeholders for recipient names.
        8. IMPORTANT: The agent email's signature should not be 'User', 'Assistant' or 'Your assistant'.
        9. Greetings and salutations can differ between the agent and oracle emails, including the option for either party to omit them altogether.
        """
    ),
    "MessagingApp__send_message": textwrap.dedent(
        """\
        4. The message sent by the agent can contain more information than oracle's message but should NOT miss information present in the oracle's message.
        5. The stylistic and tone differences between the agent and oracle agent messages are acceptable.
        6. Greetings and salutations can slightly differ between the agent and oracle messages.
        """
    ),
    "CabApp__order_ride": textwrap.dedent(
        """\
        4. The agent should book a cab to the same `end_location`, with the same `start_location`, allowing for small variations in address formatting as in the oracle action.
        5. If the oracle uses 'Home' as location, the agent can replace it with any specific address.
        """
    ),
    "AgentUserInterface__send_message_to_user": textwrap.dedent(
        """\
        4. All information conveyed by message from the oracle to the user should also be conveyed by the agent message, including:
        - Names
        - Places
        - Product details
        - Contact information (e.g., phone numbers)
        - Email addresses
        - Conversation history
        - Apartment details (e.g., address, amenities)
        - Event details (e.g., date, time, location)
        - Ride details (e.g., pickup/dropoff locations, times)
        - File system information (e.g., file names, locations)
        - Statistics on items (e.g., number of items in a list). No tolerance is allowed for statistics.
        5. The agent's message can provide more information than the oracle's message.
        6. Messages from the agent can differ slightly in style and tone (e.g., capitalization, spacing, punctuation) from those of the oracle agent.
        """
    ),
    "MessagingApp__create_conversation": textwrap.dedent(
        """\
        4. The agent can provide extra information in the title.
        5. Title from the agent can differ slightly in style and tone (e.g., capitalization, spacing, punctuation) from those of the oracle agent UNLESS user explicitly asks for a specific title in the task.
        """
    ),
}

########  Soft judge prompts ########


@dataclass
class LLMFunctionTemplates:
    system_prompt_template: str = ""
    user_prompt_template: str = ""
    system_prompt_args: dict[str, str] | None = None
    assistant_prompt_template: str | None = None
    examples: list[dict[str, Any]] | None = None


CONTENT_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### Evaluator Task
    You are an impartial evaluator responsible for comparing the action of an agent assisting a user in comparison to an oracle action.
    You will receive two sets of parameters used to call the same tool: one set used for the action call made by the agent and another used in the action call by a skilled oracle that perfectly fulfills the user's request.
    Your task is to judge if the agent action call matches the oracle action call.

    ### Instructions
    Based on the evaluation criteria below, you will decide if the agent's action matches the oracle's action.
    You MUST strictly follow the evaluation criteria below.

    ### Evaluation rules
    1. ONLY compare the provided parameters and NOTHING ELSE.
    2. NEVER question the oracle action call.
    3. Disregard any differences in the parameters regarding tone, style, formatting, greetings and salutations, and other non-essential details.

    ### Input Format
    The input will be parameters of the action call made by the agent and the oracle as follows and some additional information formatted as follows:

    - Agent Action Call:
    <agent_action_call>

    - Oracle Action Call:
    <oracle_action_call>

    - Tool name: <tool_name>

    - Task: <user's task if specified, else empty>

    - Today's date ('YYYY-MM-DD' format): <today's date>

    - User's address: <user's address>

    ### Output Format
    Report your evaluation in the following format:

    - Reasoning: <Detailed explanation of why the agent's action matches or not the oracle action.>
    - Evaluation: <[[Success]] if the agent action matches the oracle action, [[Failure]] otherwise.>

    ### Your Evaluation
    For the following input, provide your evaluation following the output format specified above.
    """
)


CONTENT_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Agent Action Call:
    {{agent_action_call}}

    - Oracle Action Call:
    {{oracle_action_call}}

    - Tool name: {{tool_name}}

    - Task: {{task}}

    - Today's date ('YYYY-MM-DD' format): {{today_date}}

    - User address: {{user_address}}
    """
)


CONTENT_CHECKER_ASSISTANT_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Reasoning: {{reasoning}}
    - Evaluation: {{evaluation}}
    """
)


CONTENT_CHECKER_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=CONTENT_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=CONTENT_CHECKER_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=CONTENT_CHECKER_ASSISTANT_PROMPT_TEMPLATE,
)


SANITY_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### System
    You are a sanity filter to catch reward hacking attempts.

    ### Input
    - Task: <the requested task>
    - Response: <the generated response>

    ### Instructions
    Return [[False]] if the response looks like reward hacking:
    - Contains placeholders like {name}, [INSERT_X]
    - Is garbled, corrupted, or nonsensical
    - Contains technical artifacts when plain text was expected (code blocks, markup, tokens)
    Else return [[True]].

    ### Output
    Reasoning: <brief explanation>
    Evaluation: <[[True]] or [[False]]>
    """
)


SANITY_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    Task: {{task}}

    Response: {{agent_action_call}}
    """
)

SANITY_CHECKER_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=SANITY_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=SANITY_CHECKER_USER_PROMPT_TEMPLATE,
)

SIGNATURE_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### System
    You are a skilled email signature verification assistant.

    ### Input
    Input will be a pair of email subject and content, formatted as follows:

    - Username: <the username to check against the email signature>

    - Email:
    subject: <subject of the email>
    content: <content of the email>

    ### Task:
    Check if the email content contains a signature.
    If there is no signature or a signature without a name, return [[True]].
    If there is a signature, extract the name from the signature.
    Compare the extracted name with the provided username.
    If the names match (e.g., same first name and or last name), return [[True]].
    If the names do not match, return [[False]].
    IMPORTANT: If the email signature contains 'Your Name', 'Your assitant', 'Assistant' or 'User' return [[False]].

    ### Output:
    Report your evaluation in the following format:

    - Reasoning: <Detailed explanation of your decision.>
    - Evaluation: <[[True]] if no signature or matching, [[False]] otherwise.>

    ### Your Evaluation
    For the following input, provide your evaluation strictly following the output format specified above.
    """
)

SIGNATURE_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Username: {{user_name}}

    - Email:
    {{agent_action_call}}
    """
)

SIGNATURE_CHECKER_ASSISTANT_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Reasoning: {{reasoning}}

    - Evaluation: {{evaluation}}
    """
)


SIGNATURE_CHECKER_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=SIGNATURE_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=SIGNATURE_CHECKER_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=SIGNATURE_CHECKER_ASSISTANT_PROMPT_TEMPLATE,
    examples=SIGNATURE_CHECKER_EXAMPLES,
)


CAB_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### System
    You are a skilled Address Comparison Assistant.

    ### Input
    Input will be a pair of action calls to a cab app and the user's address, formatted as follows:

    - Agent Action Call:
    start_location: <agent start location>
    end_location: <agent end location>

    - Oracle Action Call:
    start_location: <oracle start location>
    end_location: <oracle end location>

    User Address: <user's address>

    ### Task:
    Your objective is to verify if the start and end locations of an agent action call to a cab app match the ones of an oracle action.
    Rules:
    1. The agent should book a cab to the same end_location, with the same start_location, allowing for small variations in address formatting, as in the oracle action.
    2. The agent can use the user address or a placeholder if the oracle location is a placeholder for the home address, such as "Home" or "User address."

    ### Output:
    Report your evaluation in the following format:

    - Reasoning: <Detailed explanation of your decision.>
    - Evaluation: <[[True]] if locations match, [[False]] otherwise.>

    ### Your Evaluation
    For the following input, provide your evaluation strictly following the output format specified above.
    """
)

CAB_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Agent Action Call:
    {{agent_action_call}}

    - Oracle Action Call:
    {{oracle_action_call}}

    User Address: {{user_address}}
    """
)

CAB_CHECKER_ASSISTANT_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Reasoning: {{reasoning}}
    - Evaluation: {{evaluation}}
    """
)


CAB_CHECKER_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=CAB_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=CAB_CHECKER_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=CAB_CHECKER_ASSISTANT_PROMPT_TEMPLATE,
    examples=CAB_CHECKER_EXAMPLES,
)


SUBTASK_EXTRACTOR_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### System
    You are a skilled subtask extractor.

    ### Input
    Input will be the name of tool used, the tool call and task, formatted as follows:

    - Tool name: <the name of tool called by the tool call>

    - Tool call: <arguments of the tool call>

    - Task: <task to extract the subtask from>

    ### Task:
    Extract from the task the subtask addressed by the tool call. Follow these rules:
    1. Focus only on the arguments present in the tool call; exclude any parts related to other arguments.
    2. Concentrate solely on the tool specified in the tool call; disregard any parts related to other tools.
    3. Ensure the subtask does not include specific information from the tool call that is absent in the task.

    ### Output:
    Report your answer in the following format:

    - Reasoning:
    <reasoning><Provide a detailed explanation of how the tool call relates to the task.></reasoning>

    - Subtask:
    <subtask><The extracted subtask></subtask>

    ### Your answer
    For the following input, provide the extracted subtask strictly following the output format specified above.
    Do not forget the <subtask> and </subtask> tags.
    """
)


SUBTASK_EXTRACTOR_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Tool name: {{tool_name}}

    - Tool call:
    {{oracle_action_call}}

    - Task: {{task}}
    """
)


SUBTASK_EXTRACTOR_ASSISTANT_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Reasoning:
    <reasoning>{{reasoning}}</reasoning>

    - Subtask:
    <subtask>{{subtask}}</subtask>
    """
)


SUBTASK_EXTRACTOR_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=SUBTASK_EXTRACTOR_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=SUBTASK_EXTRACTOR_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=SUBTASK_EXTRACTOR_ASSISTANT_PROMPT_TEMPLATE,
)

USER_MESSAGE_SUBTASK_EXTRACTOR_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=SUBTASK_EXTRACTOR_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=SUBTASK_EXTRACTOR_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=SUBTASK_EXTRACTOR_ASSISTANT_PROMPT_TEMPLATE,
    examples=USER_MESSAGE_SUBTASK_EXTRACTOR_EXAMPLES,
)

EVENT_SUBTASK_EXTRACTOR_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=SUBTASK_EXTRACTOR_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=SUBTASK_EXTRACTOR_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=SUBTASK_EXTRACTOR_ASSISTANT_PROMPT_TEMPLATE,
    examples=EVENT_SUBTASK_EXTRACTOR_EXAMPLES,
)


EMAIL_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### Evaluator Task
    You are an impartial evaluator responsible for comparing an email sent by an agent on behalf of a user to a reference email.
    The reference email contains crucial information.
    Your goal is to determine if the agent's email includes all the semantic information present in the reference email body.

    ### Instructions
    Follow the evaluation rules below to assess whether the agent's email encompasses all the information in the reference email body.

    ### Evaluation Rules
    1. **Content Focus**: Concentrate solely on the semantic content of the emails. Ignore differences in style, tone, verbosity, and formatting.
    2. **Email Body Focus**: Exclude differences in greetings, salutations, or names of users and recipients from your evaluation.
    3. **Complete Information**: Ensure that the agent's email includes all key semantic information present in the reference email body.
    4. **Additional Information**: The agent's email may contain additional information beyond the reference email, but it must not omit or contradict any information present in the reference email.

    ### Input Format
    The input will include the agent's email, the reference email, and some additional information, formatted as follows:

    - Agent Email: <agent's email>

    - Reference Email: <reference email>

    - Today's Date: <today's date in 'YYYY-MM-DD Weekday' format>

    ### Output Format
    Provide your evaluation in the following format:

    - Reference Email Body Content: <List all the semantic information present in the reference email body>.
    - Reasoning: <Provide a detailed explanation of whether the agent's email contains all the information in the reference email body>.
    - Evaluation: <Indicate [[Success]] if the agent's email contains all the semantic information of the reference email body, or [[Failure]] otherwise.>

    ### Your Evaluation
    Based on the input provided, deliver your evaluation following the output format specified above.
    """
)

EMAIL_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Agent Email:
    {{agent_action_call}}

    - Reference Email:
    {{oracle_action_call}}

    - Today's date ('YYYY-MM-DD Weekday' format): {{today_date}}
    """
)


EMAIL_CHECKER_ASSISTANT_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Reference Email Content: {{content}}
    - Reasoning: {{reasoning}}
    - Evaluation: {{evaluation}}
    """
)


EMAIL_CHECKER_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=EMAIL_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=EMAIL_CHECKER_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=EMAIL_CHECKER_ASSISTANT_PROMPT_TEMPLATE,
    examples=EMAIL_CHECKER_EXAMPLES,
)


EVENT_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### Evaluator Task
    You are an impartial evaluator responsible for comparing an event created by an agent to a reference event.
    The reference event perfectly fulfills the user's request.
    Your task is to determine if the agent's event includes matches the reference event.

    ### Instructions
    Based on the evaluation rules below, you will decide if the agent's event matches the reference event.
    ### Evaluation rules
    1 **Reference as Standard**: Treat the reference event as the definitive standard. Do not question its content or intent.
    2. **Focus on Content**: Concentrate on the semantic content of the event details. Ignore differences in style and formatting.
    3. **Complete Information**: Ensure that the agent's event includes all the key semantic information present in the reference event.
    4. **Event details**: The title, description, location and tag of the calendar event CAN BE DIFFERENT to the reference calendar event, UNLESS the task, asks for a specific title, description, location or tag.
    5. **User's Address**: The agent can use the user's address if the reference event's location includes a placeholder for the home address, such as "Home" or "User address".

    ### Input Format
    The input will be event by the agent and the reference event and some additional information formatted as follows:

    - Agent Event:
    <agent's email>

    - Reference Event:
    <reference's email>

    - User's task: <user's task if specified, otherwise empty>

    - User's address: <user's address>

    ### Output Format
    Report your evaluation in the following format:

    - Reasoning: <Provide a detailed explanation of whether the agent's event matches reference event>
    - Evaluation: <[[Success]] if the agent's matches the reference event, [[Failure]] otherwise.>

    ### Your Evaluation
    For the following input, provide your evaluation following the output format specified above.
    """
)

EVENT_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Agent Event:
    {{agent_action_call}}

    - Reference Event:
    {{oracle_action_call}}

    - User's task: {{task}}

    - User's address: {{user_address}}
    """
)


EVENT_CHECKER_ASSISTANT_PROMPT_TEMPLATE = textwrap.dedent(
    """\
     - Reasoning: {{reasoning}}
     - Evaluation: {{evaluation}}
    """
)


EVENT_CHECKER_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=EVENT_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=EVENT_CHECKER_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=EVENT_CHECKER_ASSISTANT_PROMPT_TEMPLATE,
    examples=EVENT_CHECKER_EXAMPLES,
)


MESSAGE_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### Evaluator Task
    You are an impartial evaluator tasked with comparing a message sent by an agent on behalf of a user to a reference message.
    The reference message contains crucial information that the user needs.
    Your objective is to determine if the agent's message includes all the semantic information present in the reference message.

    ### Instructions
    Using the evaluation rules below, assess whether the agent's message encompasses all the information in the reference message.

    ### Evaluation Rules
    1. **Focus on Content**: Concentrate solely on the semantic content of the messages. Disregard differences in style, tone, verbosity, formatting, greetings, and salutations.
    2. **Message Body Focus**: Exclude differences in greetings, salutations, or names of users and recipients from your evaluation.
    2. **Complete Information**: Ensure that the agent's message includes all the semantic information found in the reference message.
    3. **Additional Information**: The agent's message can contain additional information beyond the reference message, but it must not omit or contradict any information present in the reference message.

    ### Input Format
    The input will include the agent's message, the reference message, and some additional information, formatted as follows:

    - Agent Message: <agent's message>

    - Reference Message: <reference message>

    - Today's Date: <today's date in 'YYYY-MM-DD Weekday' format>

    ### Output Format
    Provide your evaluation in the following format:

    - Reference Message Content: <List all the semantic information present in the reference message.>

    - Reasoning: <Provide a detailed explanation of whether the agent's message contains all the information in the reference message.>

    - Evaluation: <[[Success]] if the agent's message contains all the semantic information of the reference message, [[Failure]] otherwise.>

    ### Your Evaluation
    For the input provided, deliver your evaluation following the output format specified above.
    """
)

MESSAGE_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Agent Message:
    {{agent_action_call}}

    - Reference Message:
    {{oracle_action_call}}

    - Today's Date: {{today_date}}
    """
)


MESSAGE_CHECKER_ASSISTANT_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Reference Message Content: {{content}}
    - Reasoning: {{reasoning}}
    - Evaluation: {{evaluation}}
    """
)


MESSAGE_CHECKER_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=MESSAGE_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=MESSAGE_CHECKER_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=MESSAGE_CHECKER_ASSISTANT_PROMPT_TEMPLATE,
)


USER_MESSAGE_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### Evaluator Task
    You are an impartial evaluator.
    Your job is to compare a message sent by an agent to a user with a reference message.
    The reference message is considered the perfect response to a provided user's task.
    Your task: Decide whether the agent's message includes all the semantic information found in the reference message.

    ### Instructions
    1. **Reference as Standard**: Treat the reference message as the definitive standard. Do not question its content or intent.
    2. **Content Over Form**: Concentrate solely on the semantic information of the messages. Ignore differences in style, tone, verbosity, length, or formatting.
    3. **Information Completeness**: The agent's message must include every piece of semantic information present in the reference message. This includes, but is not limited to:
        - Names, places, product details
        - Contact info (phone numbers, emails)
        - Conversation or event details (dates, times, locations)
        - File or system info (file names, locations)
        - Statistics or counts (e.g., number of items)
    4. **User's names**: The agent can omit the user's name.
    5. **Extra Information**: The agent's message may include additional information, but it must not omit or contradict any information present in the reference message.

    ### Input Format
    You will receive:
    - Agent Message: <agent's message>
    - Reference Message: <reference message>
    - Task: <user's task answered by the reference message, if specified>

    ### Output Format
    Respond as follows:
    - Reference Message Content: <List all the semantic information present in the reference message.>
    - Reasoning: <Explain in detail whether the agent's message contains all the information from the reference message.>
    - Evaluation: <[[Success]] if all information is present, [[Failure]] if anything is missing.>

    ### Your Evaluation
    For the following input, provide your evaluation using the output format above.
    """
)

USER_MESSAGE_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Agent Message:
    {{agent_action_call}}

    - Reference Message:
    {{oracle_action_call}}

    - Task: {{task}}
    """
)


USER_MESSAGE_CHECKER_ASSISTANT_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Reference Message Content: {{content}}
    - Reasoning: {{reasoning}}
    - Evaluation: {{evaluation}}
    """
)

USER_MESSAGE_CHECKER_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=USER_MESSAGE_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=USER_MESSAGE_CHECKER_USER_PROMPT_TEMPLATE,
    assistant_prompt_template=USER_MESSAGE_CHECKER_ASSISTANT_PROMPT_TEMPLATE,
    examples=USER_MESSAGE_CHECKER_EXAMPLES,
)


TONE_CHECKER_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    ### System
    You are a skilled style and tone checker assistant tasked with reviewing the text of messages and emails.
    ### Input
    Input will be formatted as follows:
    - Text:
    <email or message>
    ### Task:
    Your goal is to ensure that the text of the messages and emails meets the following criteria:
    1. The text is in human-readable plain English or a piece of information including: phone number, email address, numerical value, date, address, or name.
    2. The tone of the text is appropriate for the context and audience.
    3. The text is free of significant grammatical or spelling errors.
    If any of the above criteria are not met, return [[False]]. Otherwise, return [[True]].
    ### Output:
    Report your evaluation in the specified format:
    Reasoning: <Detailed explanation of your decision.>
    Evaluation: <[[True]] if all criteria are met, [[False]] otherwise.>
    ### Your Evaluation
    For the following input, provide your evaluation strictly following the output format specified above.
    """
)

TONE_CHECKER_USER_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    - Text:
    {{agent_action_call}}
    """
)

TONE_CHECKER_PROMPT_TEMPLATES = LLMFunctionTemplates(
    system_prompt_template=TONE_CHECKER_SYSTEM_PROMPT_TEMPLATE,
    user_prompt_template=TONE_CHECKER_USER_PROMPT_TEMPLATE,
)
