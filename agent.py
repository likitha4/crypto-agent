import os
import json
from dotenv import load_dotenv
from groq import Groq
from tools import get_coin_prices, suggest_coins

load_dotenv()

client = Groq(api_key= os.getenv("GROQ_API_KEY"))

tools= [
    {
        "type":"function",
        "function": {
            "name":"get_coin_prices",
            "description":"Get current prices and 24h change for cryptocurrencies. Use this when the user asks about prices.",
            "parameters":{
                "type":"object",
                "properties":{
                    "coin_ids":{
                        "type":"array",
                        "items":{"type":"string"},
                        "description":"List of coin ids like bitcoin, ethereum, solana"
                    }
                },
                "required":[]
            }
        }
    },
     {
        "type":"function",
        "function": {
            "name":"suggest_coins",
            "description":"Suggest beginner-friendly or interesting coins based on market data. Use when the user asks about suggestions.",
            "parameters":{
                "type":"object",
                "properties":{
                    "limit":{
                        "type":"integer",
                        "description":"How many coins to suggest (default 5)"
                    }
                },
                "required":[]
            }
        }
    }
]

def run_agent(user_question:str)->str:
    messages =[
        {
            "role":"system",
            "content":"You are a helpful crypto assistant. Prices should be in INR when available. For price questions use get_coin_prices. For suggestions or beginner recommendations use suggest_coins. Do not use get_coin_prices when the user only asks for suggestions. Explain clearly."
        },
        {
                "role":"user",
                "content":user_question
        }
    ]
    response = client.chat.completions.create(
        model= "openai/gpt-oss-20b",
        messages= messages,
        tools= tools,
        tool_choice="auto"
    )
    message = response.choices[0].message

    if message.tool_calls:
        tool_call  = message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments or "{}")
        print("tool_calls", message.tool_calls)

        if  function_name == "get_coin_prices":
            coin_ids = arguments.get("coin_ids")
            tool_result= get_coin_prices(coin_ids)
        
        elif function_name == "suggest_coins":
            limit = arguments.get("limit",5)
            tool_result = suggest_coins(limit)

        else:
            tool_result ={"error":f"Unknown tool :{function_name}"}
            print("ABOUT TO APPEND TOOL RESULT")

        messages.append(message)
        messages.append({
            "role":"tool",
            "tool_call_id":tool_call.id,
            "name": function_name,
            "content":json.dumps(tool_result)
            })
        print("tool_result:", tool_result)
        
        final_response = client.chat.completions.create(
            model= "qwen/qwen3.8-27b",
            messages=messages,
            tools= tools,
            tool_choice="auto"
        )   
        text =  final_response.choices[0].message.content
        return text or "Sorry, I could not generate a suggestion right now."

    return message.content or "Sorry, I could not answer that"