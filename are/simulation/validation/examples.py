# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import textwrap

USER_MESSAGE_SUBTASK_EXTRACTOR_EXAMPLES = [
    {
        "input": {
            "tool_name": "AgentUserInterface__send_message_to_user",
            "oracle_action_call": textwrap.dedent(
                """\
                content: Augustín Moreno-Sánchez
                """
            ),
            "task": textwrap.dedent(
                """\
                Tell me only the name of the youngest person I have emailed this month who is not in any of my WhatsApp conversations but is in at least one in Messenger. If there is a tie, choose the one based on first name in alphabetical order.
                """
            ),
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The tool call indicates that the task is to send a message to the user containing a specific name, which is "Augustín Moreno-Sánchez." This implies that the task involves identifying this individual's name based on specific criteria and communicating that information to the user. The criteria involve the individual's age, email interaction, absence from WhatsApp conversations, and presence in Messenger conversations. Among the individuals fitting these criteria, the name is selected based on alphabetical order in case of a tie.
                """
            ),
            "subtask": textwrap.dedent(
                """\
                Communicate to the user the name of the youngest person emailed this month, not in WhatsApp but in Messenger, chosen based on alphabetical order if needed.
                """
            ),
        },
    },
    {
        "input": {
            "tool_name": "AgentUserInterface__send_message_to_user",
            "oracle_action_call": textwrap.dedent(
                """\
                content: 6
                """
            ),
            "task": textwrap.dedent(
                """\
                Identify the average attendee age from the August Networking Events that took place on the same days that I had scheduled Free Time. Do not include me in the calculation. Round that value to the nearest whole number and tell me how many contacts I have who are within 3 years of the number.
                """
            ),
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The task involves several steps including identifying average attendee age, rounding it to the nearest whole number, and determining the number of contacts within 3 years of that number. The tool call is for "AgentUserInterface__send_message_to_user" with the content "6". This implies that the subtask is related to sending a message to the user. Given the task context, the message to be sent is likely the final result.
                """
            ),
            "subtask": textwrap.dedent(
                """\
                Tell me how many contacts I have who are within 3 years of the calculated average age.
                """
            ),
        },
    },
]


EVENT_SUBTASK_EXTRACTOR_EXAMPLES = [
    {
        "input": {
            "tool_name": "CalendarApp__add_calendar_event",
            "oracle_action_call": textwrap.dedent(
                """\
                title: Research Time
                description: Time allocated for research and study.
                """
            ),
            "task": textwrap.dedent(
                """\
                I am unable to perform any physical activities for the rest of this week as I have a back spasm. Please cancel all yoga events that are scheduled for the rest of this week. Also, I would like to spend the freed time on research, so please add "Research Time" events in the place of the cancelled yoga events. Send a group email to the attendees of yesterday's Research Meeting and ask them what topics they are researching.
                """
            ),
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The tool call is for the Calendar__add_calendar_event tool, with the title "Research Time" and description "Time allocated for research and study." This suggests that the subtask is related to adding a new event to the calendar. Looking at the task, it mentions adding "Research Time" events in place of the cancelled yoga events. This indicates that the subtask is to add these specific events to the calendar, which aligns with the tool call's details.
                """
            ),
            "subtask": textwrap.dedent(
                """\
                Add "Research Time" event to the calendar in place of cancelled yoga event.
                """
            ),
        },
    },
    {
        "input": {
            "tool_name": "CalendarApp__add_calendar_event",
            "oracle_action_call": textwrap.dedent(
                """\
                title: Inspection Day
                """
            ),
            "task": textwrap.dedent(
                """\
                Save all unsaved properties that are listed as 800 sqft and add an inspection day event to my calendar from 9 AM to 4 PM on the next Sunday with no events scheduled on that day.
                """
            ),
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The tool call is for the Calendar__add_calendar_event tool with the title "Inspection Day". This suggests that the subtask we are looking for is related to adding an event to the calendar. The task mentions adding an "inspection day event" to the calendar, which aligns with the title in the tool call. Therefore, we can infer that the subtask is about adding this specific event to the calendar.
                """
            ),
            "subtask": textwrap.dedent(
                """\
                Add an inspection day event to my calendar.
                """
            ),
        },
    },
]


CAB_CHECKER_EXAMPLES = [
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                start_location: 1234 NW 23rd Ave, Portland, OR 97210
                end_location: 1423 SE Division St, Portland, OR 97202
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                start_location: Home
                end_location: 1423 SE Division St, Portland, OR 97202
                """
            ),
            "user_address": "1234 NW 23rd Ave, Portland, OR 97210",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The agent's end_location, "1423 SE Division St, Portland, OR 97202", matches the oracle's end_location exactly. The agent's start_location, "1234 NW 23rd Ave, Portland, OR 97210", does not match the oracle's start_location, "Home". However, according to the task, if the oracle uses 'Home' as a location, the agent can replace it with user's address. Since the agent has provided the user's address as the start_location, and the end_location matches, the locations can be considered as matching.
                """
            ),
            "evaluation": "[[True]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                start_location: Mittlere Strasse 12, 4058 Basel, Switzerland
                end_location: Rue de Lausanne 45, Geneva, Switzerland
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                start_location: Home
                end_location: Rue de Lausanne 45, Geneva
                """
            ),
            "user_address": "Mittlere Strasse 12, 4058 Basel, Switzerland",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The agent's start_location is "Mittlere Strasse 12, 4058 Basel, Switzerland", which matches the user's address. The oracle's start_location is "Home", which is a placeholder for the user's home address. Since the user's address matches the agent's start_location, this part of the comparison is valid. The agent's end_location is "Rue de Lausanne 45, Geneva, Switzerland", and the oracle's end_location is "Rue de Lausanne 45, Geneva". Although there is a slight variation in formatting (the agent includes the country "Switzerland" while the oracle does not), the essential address information matches. Therefore, both the start and end locations of the agent action call effectively match those of the oracle action call, considering the allowed variations in address formatting and the use of placeholders for the home address.
                """
            ),
            "evaluation": "[[True]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                start_location: Kungsgatan 37, 411 19 Göteborg
                end_location: Linnégatan 1, 413 04 Göteborg
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                start_location: Kungsgatan 37, 411 19 Göteborg
                end_location: Linnégatan 12, 413 04 Göteborg
                """
            ),
            "user_address": "Drottninggatan 59, 111 21 Stockholm",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The agent action call and the oracle action call have the same start_location, which is "Kungsgatan 37, 411 19 Göteborg". However, the end_locations differ. The agent's end_location is "Linnégatan 1, 413 04 Göteborg", while the oracle's end_location is "Linnégatan 12, 413 04 Göteborg". Although the street names and postal codes match, the house numbers are different (1 vs 12). Since the task allows for small variations in address formatting, this discrepancy in house numbers indicates the locations do not match exactly as required.
                """
            ),
            "evaluation": "[[False]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                start_location:  Praias Brancas, 4470-558 Vila Nova da Telha
                end_location: Rua do Almada, 147, 4050-036 Porto, Portugal
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                start_location: Pedras Rubras, 4470-558 Vila Nova da Telha
                end_location: Rua do Almada, 147, 4050-036 Porto, Portugal
                """
            ),
            "user_address": "Avenida da Liberdade 144, 1250-146 Lisboa",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The agent action call and the oracle action call have different start_locations. Although they share the same postal code, indicating they are in the same general area, the specific locations ("Praias Brancas" vs "Pedras Rubras") do not match.
                """
            ),
            "evaluation": "[[False]]",
        },
    },
]


SIGNATURE_CHECKER_EXAMPLES = [
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                subject: UPDATED: Property Viewing and Cab Booking Confirmation
                content: Dear Astrid,
                Thank you for your reply. I have updated the arrangements as per your request:
                Changed the property to view: Herning City Living - The unfurnished 1-bedroom condo located at Torvegade 20, Herning (7400), priced at 800 per month.
                Rescheduled the premium cab to pick you up tomorrow (Wednesday, October 16th) at 10:00 AM from your address (Østerbrogade 27, København Ø) to take you to the unfurnished property. The updated ride details are:
                Ride ID: 9559c4a0c3ba4e0da3e2c6a74bca8c24
                Service Type: Premium
                Pickup time: 10:00 AM, October 16th, 2024
                Estimated fare: $38.96
                As requested, I am sending this confirmation via email and will also send a message on our 1-on-1 Messenger chat.
                Please let me know if you need any further adjustments.
                Best regards,
                Assistant
                """
            ),
            "user_name": "Søren Kjær",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The email content contains a signature with the name "Assistant". According to the task, if the 'Your assistant', 'Assistant' or 'User' is in the email signature, the evaluation should return False. Therefore, the presence of "Assistant" in the signature is sufficient to conclude the evaluation.
                """
            ),
            "evaluation": "[[False]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                subject: Kaveri Apartments Viewing Appointment - Tuesday, Oct 22 at 10:30 AM
                content: Dear Ravindra,

                I hope this email finds you well. I'm writing to confirm our viewing appointment at Kaveri Apartments (Chennai, Tamil Nadu) scheduled for next Tuesday, October 22, 2024, from 10:30 AM to 11:30 AM.

                The property is a 2-bedroom, 1-bathroom apartment with 900 sq ft, unfurnished on the upper floors. It includes amenities like parking and laundry facilities.

                Please let me know if you need any additional information or if there are any changes to the schedule.

                Looking forward to meeting you at the property.

                Best regards,
                Jasmine
                """
            ),
            "user_name": "Rohan Kumar",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The email content contains a signature with the name "Assistant". According to the task, if the 'Your assistant', 'Assistant' or 'User' is in the email signature, the evaluation should return False. Therefore, the presence of "Assistant" in the signature is sufficient to conclude the evaluation.
                """
            ),
            "evaluation": "[[False]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                content: Hi Takashi, I'd be happy to collaborate on a project with you. My free days over the next two weeks are Monday, Tuesday, Thursday, and Sunday. Let me know which day works best for you to meet up and brainstorm some ideas.
                """
            ),
            "user_name": "Ali Hassan",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The email content does not contain a signature. There is no name or any indication of a signature at the end of the email.
                """
            ),
            "evaluation": "[[True]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                subject: Travel Enquiry
                content: Dear Klaasje,

                I hope this email finds you well. I am planning a trip to Melbourne and was wondering if you might still have connections with your old employer that could help me get some cheap deals.

                I've set aside some time this Saturday, October 19, from 5:00 PM to 6:00 PM for a 'Travel Enquiring' session, and I would be keen to have a call with you during this time if you're available.

                Looking forward to hearing from you.

                Best regards,
                Rohini
                """
            ),
            "user_name": "Rohini Deshpande",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The email content contains a signature with the name "Rohini", which matches the first name of the provided username "Rohini Deshpande". Since the names match, the evaluation is True.
                """
            ),
            "evaluation": "[[True]]",
        },
    },
]


EVENT_CHECKER_EXAMPLES = [
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                title: Wine & Crackers Gathering!
                location: 1234 NW 23rd Ave, Portland, OR 97210
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                title: Wine & Crackers Gathering!
                location: Home
                """
            ),
            "task": "Schedule the 'Wine & Crackers Gathering!' event on the calendar",
            "user_address": "1234 NW 23rd Ave, Portland, OR 97210",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The agent's event title matches the reference event title, which is "Wine & Crackers Gathering!". The location in the reference event is "Home", which is a placeholder for the user's home address. The user's address is provided as "1234 NW 23rd Ave, Portland, OR 97210", which is the same location used by the agent. According to the evaluation rules, the agent can use the user's address if the reference event's location includes a placeholder for the home address. Since the agent's event location matches the user's address and the title matches the reference event title, the agent's event includes all the key semantic information present in the reference event.
                """
            ),
            "evaluation": "[[Success]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                title: Research Meeting
                description: Conduct research on ongoing projects and read relevant literature.
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                title: Research Time
                description: Time allocated for research purposes.
                """
            ),
            "task": "Add a 'Research Time' calendar event to replace a cancelled yoga event",
            "user_address": "4567 NE 45th St, Seattle, WA 98101",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The agent's event has a title "Research Meeting" which is different from the reference event's title "Research Time". However, according to the evaluation rules, the title can be different unless the task specifically asks for a certain title. In this case, the user's task does ask for a 'Research Time' calendar event, so the title should match. The description of the agent's event, "Conduct research on ongoing projects and read relevant literature", provides more specific details about the research activity compared to the reference event's description, "Time allocated for research purposes". Since the task specifically asks for a 'Research Time' event, the agent's event does not match the reference event due to the title mismatch.
                """
            ),
            "evaluation": "[[Failure]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                title: Dinner with Family
                description: Spend quality time with family.
                location: Tiensestraat 39, 3000 Leuven
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                title: Dinner with Family
                description: Spend quality time with family.
                location: Place Saint-Lambert, 4000 Liege, Belgium
                """
            ),
            "tool_name": "Calendar__add_calendar_event",
            "task": "Reschedule the Dinner with Family event by changing its location to the destination of the cab ride taken on October 11th",
            "user_address": "Rue de l'Église 12, 1000 Bruxelles, Belgium",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The agent's event has the same title and description as the reference event, which matches the requirements. However, the location in the agent's event is "Tiensestraat 39, 3000 Leuven", whereas the reference event's location is "Place Saint-Lambert, 4000 Liege, Belgium". The user's task specifies that the location should be changed to the destination of the cab ride taken on October 11th, which must be the one in the reference event. Since the location in the agent's event does not match the location in the reference event we conclude that the agent's event does not matches the reference event.
                """
            ),
            "evaluation": "[[Failure]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                title: Yoga Class
                description: 45-minute yoga class with a certified instructor.
                tag: Yoga
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                title: Yoga Session
                description: yoga class.
                tag: Wellness
                """
            ),
            "tool_name": "Calendar__add_calendar_event",
            "task": "Schedule a yoga class for 45 minutes with a certified instructor",
            "user_address": "67 Main St, Anytown, USA",
        },
        "output": {
            "reasoning": textwrap.dedent(
                """\
                The agent's event title is "Yoga Class" while the reference event title is "Yoga Session". Although the titles are not identical, they convey the same semantic meaning. The agent's event description is "45-minute yoga class with a certified instructor", which matches the user's task of scheduling a "45-minute yoga class with a certified instructor". The reference event description is simply "yoga class", which is less detailed but still conveys the main activity. The tags are different, with the agent's event tagged as "Yoga" and the reference event tagged as "Wellness". However, since the task does not specify a particular tag, this difference is acceptable according to the evaluation rules. The agent's event includes all the key semantic information present in the reference event and the user's task, which is the main criterion for evaluation.
                """
            ),
            "evaluation": "[[Success]]",
        },
    },
]


USER_MESSAGE_CHECKER_EXAMPLES = [
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                content: You had 1 dinner appointment with Søren Mikkelsen last month.
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                content: 2
                """
            ),
            "task": "Inform the user of the number of dinner appointments last month with the contact matching the specified name and location criteria",
        },
        "output": {
            "content": textwrap.dedent(
                """\
                The number of dinner appointments last month is specified as 2.
                """
            ),
            "reasoning": textwrap.dedent(
                """\
                The reference message indicates that there were 2 dinner appointments last month, which suggests that the number of appointments is the key piece of information. In contrast, the agent's message states that there was 1 dinner appointment with Søren Mikkelsen last month. This discrepancy suggests that the agent's message does not include all the semantic information found in the reference message, specifically the correct number of dinner appointments.
                """
            ),
            "evaluation": "[[Failure]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                content: I have updated the job details for all 7 contacts living in France to 'Teacher'. I'm ready to order 7 guitar pinatas, but I need to know which variant you prefer. Here are the available options:

                1. Medium, Paper Mache, Brown, Candy-filled - $28.64
                2. Medium, Cardboard, Brown, Candy-filled - $25.49
                3. Medium, Paper Mache, Red, Confetti-filled - $30.99

                Please let me know which variant you would like to order.
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                content: Which version of the Acoustic Guitar Pinata would you like to purchase?
                """
            ),
            "task": "Clarify the version of the Acoustic Guitar Pinata to purchase",
        },
        "output": {
            "content": textwrap.dedent(
                """\
                The task is to clarify the version of the Acoustic Guitar Pinata to purchase.
                The reference message asks the user to choose a version of the Acoustic Guitar Pinata.
                """
            ),
            "reasoning": textwrap.dedent(
                """\
                The agent's message  provide options for the user to choose from, which indirectly relates to choosing a version of the guitar pinata. The key information from the reference message is the request to choose a version of the Acoustic Guitar Pinata. The agent's message, while including this choice, specifies the options which are more detailed than the reference message's general inquiry. Despite the additional details, the core request to select a variant (or version) of the pinata is present.
                """
            ),
            "evaluation": "[[Success]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                content: I found two available versions of the Rubie's Adult Star Wars Darth Vader Glovelettes in the color black. One is made of Latex and costs $10.7, and the other is made of Faux Leather and costs $12.99. Which one would you like to buy?
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                content: Rohan, I found two versions of the Rubie's Adult Star Wars Darth Vader Glovelettes in black. Which one would you like to buy?
                """
            ),
            "task": "Ask the user to choose between two versions of the Rubie's Adult Star Wars Darth Vader Glovelettes in black",
        },
        "output": {
            "content": textwrap.dedent(
                """\
                The semantic information present in the reference message includes:
                The user's name: Rohan
                The product name: Rubie's Adult Star Wars Darth Vader Glovelettes
                The color of the product: black
                The existence of two versions of the product
                A question asking the user to choose between the two versions
                """
            ),
            "reasoning": textwrap.dedent(
                """\
                The agent's message includes the product name, color, and the task of choosing between two versions. It provides additional details not present in the reference message, such as the materials and prices of the two versions. The reference message does not mention these specifics but does include the user's name, "Rohan," which the agent's message omits. According to the guidelines, the agent can omit the user's name. The critical aspect is whether the agent's message contains all the semantic information from the reference message, which it does.
                """
            ),
            "evaluation": "[[Success]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                content: Based on my search, I found three people who have used the word 'computer' in their emails. Their email addresses are: kaarina.makinen@gmail.com, kaarlo.nieminen@student.aalto.fi, and jianzhi.wen@shsci.ac.cn. However, I couldn't find any conversations in WhatsApp with the given user IDs. If you have any further information or clarification about the person you are looking for, I may be able to help you narrow down the search.
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                content: jianzhi.wen@shsci.ac.cn
                """
            ),
            "task": "Identify and communicate the email address of the fellow computer lover who matches the specified criteria.",
        },
        "output": {
            "content": textwrap.dedent(
                """\
                The email address of the fellow computer lover who matches the specified criteria is jianzhi.wen@shsci.ac.cn.
                """
            ),
            "reasoning": textwrap.dedent(
                """\
                The reference message provides a specific email address (jianzhi.wen@shsci.ac.cn) as the answer to identifying the fellow computer lover who matches the criteria. However, the agent's message provides three different email addresses (kaarina.makinen@gmail.com, kaarlo.nieminen@student.aalto.fi, and jianzhi.wen@shsci.ac.cn) without clearly identifying which one is the correct match for the specified criteria. While the correct email address is included in the agent's list, the agent fails to definitively identify it as the answer, instead presenting it as one of three options and asking for further clarification. This does not fulfill the task requirement to "identify and communicate the email address" of the specific person who matches the criteria.
                """
            ),
            "evaluation": "[[Failure]]",
        },
    },
]


EMAIL_CHECKER_EXAMPLES = [
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                subject: Which house will you be?
                content: I've ordered you the Harry Potter Sorting Hat.
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                subject: Which house will you be?
                content: Dear Kymberley,
                I've ordered the Harry Potter Sorting Hat for you.
                Best,
                Rohan
                """
            ),
            "today_date": "2024-10-15 Tuesday",
        },
        "output": {
            "content": textwrap.dedent(
                """\
                ### Reference Email Body Content:
                1. The sender has ordered the Harry Potter Sorting Hat.
                2. The Harry Potter Sorting Hat was ordered for the recipient, Kymberley.
                """
            ),
            "reasoning": textwrap.dedent(
                """\
                The agent's email states that the sender has ordered the Harry Potter Sorting Hat for the recipient, but it does not explicitly mention the recipient's name, "Kymberley". However, the key semantic information in the reference email is that the Harry Potter Sorting Hat was ordered for the recipient. Since the agent's email implies the hat was ordered for the recipient (though without specifying the name), it captures the essential action and intent of the reference email.
                """
            ),
            "evaluation": "[[Success]]",
        },
    },
    {
        "input": {
            "agent_action_call": textwrap.dedent(
                """\
                subject: Dallas Apartment Recommendation
                content: Hi Matthew, I found an apartment in Dallas that might interest you. It's called Uptown Lofts, located at 789 Uptown Dr, Dallas, TX 75201. It's a furnished 2-bedroom, 2-bathroom apartment on the penthouse floor with amenities like a gym, pool, and laundry. The rent is $2500 per month. Would you recommend this as a good place to live when I move to Dallas?
                """
            ),
            "oracle_action_call": textwrap.dedent(
                """\
                subject: Dallas Apartment Recommendation
                content: Hi Matthew,
                Are the Uptown Lofts a good place to live when I move?
                Best,
                Aurélien
                """
            ),
            "today_date": "2024-10-15 Tuesday",
        },
        "output": {
            "content": textwrap.dedent(
                """\
                Reference Email Body Content:
                    - The email inquires about whether the Uptown Lofts are a good place to live when the sender moves to Dallas.
                """
            ),
            "reasoning": textwrap.dedent(
                """\
                The agent's email includes all the semantic information present in the reference email body, which is the inquiry about the suitability of the Uptown Lofts as a living place. Although the agent's email provides additional details about the apartment, it contains the core question posed in the reference email, thus covering all the semantic information present in the reference email body.
                """
            ),
            "evaluation": "[[Success]]",
        },
    },
]
