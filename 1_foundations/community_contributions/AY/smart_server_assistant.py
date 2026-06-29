from time import sleep

from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv(override=True)

openai = OpenAI()

is_first_call_for_auth_server = True

def check_server_status(serviceName: str) -> str:
    status =  ""
    global is_first_call_for_auth_server
    if serviceName == "auth_service":
        if is_first_call_for_auth_server:
            is_first_call_for_auth_server = False
            status = "CRITICAL: High memory usage"
    else:
        status = "HEALTHY"
    return status

def fetch_service_logs(serviceName: str) -> str:
    return "ERROR[Auth] Traceback ... OutofMemoryException: Heap limit reached on {serviceName}."

def restart_service(serviceName: str) -> bool:
    print(f"Restarting {serviceName}...")
    sleep(5)
    print(f"{serviceName} restarted successfully")
    return True

check_server_status_json = {
    "name": "check_server_status",
    "description": "Check health status of a given server or service",
    "parameters": {
        "properties": {
            "serviceName": {
                'type': 'string',
                'title': 'serviceName',
                'description': 'Name of the server'
                }
            },
        "required": ["serviceName"],
        'type': 'object',
        "additionalProperties": False
    }
}

fetch_service_logs_json = {
    "name": "fetch_service_logs",
    "description": "Get or fetch service logs of a given server or service",
    "parameters": {
        "properties": {
            "serviceName": {
                'type': 'string',
                'title': 'serviceName',
                'description': 'Name of the server'
                }
            },
        "required": ["serviceName"],
        'type': 'object',
        "additionalProperties": False
    }
}

restart_service_json = {
    "name": "restart_service",
    "description": "Restart a given server or service",
    "parameters": {
        "properties": {
            "serviceName": {
                'type': 'string',
                'title': 'serviceName',
                'description': 'Name of the server'
                }
            },
        "required": ["serviceName"],
        'type': 'object',
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": check_server_status_json},
    {"type": "function", "function": fetch_service_logs_json},
    {"type": "function", "function": restart_service_json},
    ]

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})

    return results

def service_health_check(messages):
    done = False
    response = ""
    while not done:
        response = openai.chat.completions.create(model="gpt-5.2", messages=messages, tools=tools, reasoning_effort="none")
        if response.choices[0].finish_reason == "tool_calls":
            message = response.choices[0].message
            tool_calls = message.tool_calls
            result = handle_tool_calls(tool_calls=tool_calls)
            messages.append(message)
            messages.extend(result)
        else:
            done = True
    print(response.choices[0].message.content)

system_message = """
You are asked to check and rectify the status of a server/service, check the status and rectify the issue using available tools.
Don't ask the user questions or clarifications. Provide the final output in a readable manner
"""
user_message = """"
Check up on the status of our 'auth_service'. If you notice anything wrong, dig into its logs to find the root cause, 
take the necessary actions to fix the infrastructure, and report back with a clear summary of your diagnosis and the resolution.
"""
messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]

service_health_check(messages)


