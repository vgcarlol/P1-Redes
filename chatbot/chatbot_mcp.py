# chatbot_mcp.py
import requests
import json
from llm_utils import call_llm, tools
from log_utils import log_interaction

MCP_REMOTE_URL = "http://localhost:5000/run"

def main():
    print("🤖 Chatbot MCP iniciado. Escribe 'salir' para terminar.")
    conversation_history = []

    while True:
        user_input = input("👤 Tú: ")
        if user_input.lower() == "salir":
            break

        try:
            tool_name, params = call_llm(user_input, tools, conversation_history)
            if not tool_name:
                print("🤖 No entendí tu solicitud.")
                continue

            # Llama al servidor MCP remoto
            payload = {
                "tool_name": tool_name,
                "input": params
            }

            response = requests.post(MCP_REMOTE_URL, json=payload)
            response_json = response.json()

            if "output" in response_json:
                print(f"🤖 {response_json['output']}")
                log_interaction(user_input, tool_name, params, response_json['output'])
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "tool", "content": response_json['output']})
            else:
                print(f"⚠️ Error: {response_json.get('error', {}).get('message', 'Desconocido')}")

        except Exception as e:
            print("⚠️ Error:", e)

if __name__ == "__main__":
    main()
