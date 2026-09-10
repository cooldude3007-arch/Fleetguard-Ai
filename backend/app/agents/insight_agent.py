import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.agents.tools import (
    find_part,
    get_parts,
    get_red_vehicles,
    get_high_risk_vehicles,
    get_vehicle_prediction,
    get_vehicle_rul
)


load_dotenv()


client = OpenAI(
    api_key=os.getenv(
        "OPENAI_API_KEY"
    )
)


MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)


SYSTEM_PROMPT = """
You are the FleetGuard AI Insight Agent.

You assist fleet managers with predictive
maintenance questions.

Strict rules:

1. Never invent vehicle IDs, probabilities,
   RUL values, part codes, signal values,
   risk tiers, or statistics.

2. Use the provided tools whenever the
   user asks about fleet data.

3. Only answer using information returned
   by the tools.

4. If information is unavailable, clearly
   say that it is unavailable.

5. Keep explanations concise and practical.

6. Failure probability and RUL values are
   predictive estimates, not guaranteed
   failures.

7. Do not claim that a vehicle definitely
   will or will not fail.
"""


TOOLS = [
    {
        "type": "function",
        "name": "get_parts",
        "description":
            "Get the parts monitored by FleetGuard.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "get_red_vehicles",
        "description":
            "Get Red-tier vehicles for a part.",
        "parameters": {
            "type": "object",
            "properties": {
                "part_code": {
                    "type": "string"
                }
            },
            "required": [
                "part_code"
            ],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "get_high_risk_vehicles",
        "description":
            "Get vehicles ranked by failure risk.",
        "parameters": {
            "type": "object",
            "properties": {
                "part_code": {
                    "type": "string"
                },
                "limit": {
                    "type": "integer"
                }
            },
            "required": [
                "part_code",
                "limit"
            ],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "get_vehicle_prediction",
        "description":
            "Get detailed prediction, top signals "
            "and recent trend for a VIN and part.",
        "parameters": {
            "type": "object",
            "properties": {
                "vin": {
                    "type": "string"
                },
                "part_code": {
                    "type": "string"
                }
            },
            "required": [
                "vin",
                "part_code"
            ],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "get_vehicle_rul",
        "description":
            "Get remaining useful life for "
            "a VIN and part.",
        "parameters": {
            "type": "object",
            "properties": {
                "vin": {
                    "type": "string"
                },
                "part_code": {
                    "type": "string"
                }
            },
            "required": [
                "vin",
                "part_code"
            ],
            "additionalProperties": False
        }
    },

    {
    "type": "function",

    "name": "find_part",

    "description":
        "Find the part code from a part name.",

    "parameters": {
        "type": "object",

        "properties": {
            "part_name": {
                "type": "string"
            }
        },

        "required": [
            "part_name"
        ],

        "additionalProperties": False
        }
    }

]


def execute_tool(
    db,
    name,
    arguments
):

    if name == "get_parts":

        return get_parts(
            db
        )

    if name == "get_red_vehicles":

        return get_red_vehicles(
            db,
            arguments["part_code"]
        )

    if name == "get_high_risk_vehicles":

        return get_high_risk_vehicles(
            db,
            arguments["part_code"],
            arguments["limit"]
        )

    if name == "get_vehicle_prediction":

        return get_vehicle_prediction(
            db,
            arguments["vin"],
            arguments["part_code"]
        )

    if name == "get_vehicle_rul":

        return get_vehicle_rul(
            db,
            arguments["vin"],
            arguments["part_code"]
        )

    if name == "find_part":

       return find_part(
            db,
            arguments["part_name"]
        )

    return {
        "error": "Unknown tool"
    }


def run_insight_agent(
    db,
    question,
    history=None
):

     # ---------------------------------
    # Build conversation context
    # ---------------------------------

    conversation = []

    if history:
        for message in history[-10:]:
            conversation.append(
                {
                    "role": (
                        "user"
                        if message.role == "user"
                        else "assistant"
                    ),
                    "content": message.text
                }
            )

    # Add the current question
    conversation.append(
        {
            "role": "user",
            "content": question
        }
    )

    # ---------------------------------
    # Send conversation to the model
    # ---------------------------------

    response = client.responses.create(
        model=MODEL,

        instructions=SYSTEM_PROMPT,

         input=conversation,

        tools=TOOLS
    )

    # Allow several tool calls if needed.
    for _ in range(5):

        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        if not tool_calls:
            return response.output_text

        tool_outputs = []

        for call in tool_calls:

            arguments = json.loads(
                call.arguments
            )

            result = execute_tool(
                db,
                call.name,
                arguments
            )

            tool_outputs.append(
                {
                    "type":
                        "function_call_output",

                    "call_id":
                        call.call_id,

                    "output":
                        json.dumps(
                            result,
                            default=str
                        )
                }
            )

        response = client.responses.create(
            model=MODEL,

            instructions=SYSTEM_PROMPT,

            previous_response_id=
                response.id,

            input=tool_outputs,

            tools=TOOLS
        )

    return (
        "I could not complete the request "
        "within the allowed tool-call limit."
    )