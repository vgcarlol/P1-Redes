import os
import json
import datetime
import requests
from openai import OpenAI

# ========== CONFIGURACIÓN ==========
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-3.5-turbo"

MCP_ENDPOINTS = {
    "local": "http://localhost:6000",
    "remoto": "https://mcp-remoto-783329965527.us-central1.run.app"
}

LOG_PATH = "interactions.log"

client = OpenAI(api_key=OPENAI_API_KEY)

# ========== UTILIDADES ==========
def log_interaction(prompt, tool_name, params, result):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{timestamp}]\n"
        f"Usuario: {prompt}\n"
        f"Tool usada: {tool_name}\n"
        f"Parámetros: {params}\n"
        f"Respuesta: {result}\n"
        f"{'-'*40}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)

def fetch_tools(alias, base_url):
    """Obtiene tools de un servidor MCP y las 'namespacea' con alias__."""
    try:
        r = requests.post(f"{base_url}/describe", timeout=10)
        r.raise_for_status()
        tools = r.json().get("tools", [])
        wrapped = []
        for t in tools:
            wrapped.append({
                "type": "function",
                "function": {
                    "name": f"{alias}__{t['name']}",
                    "description": f"[{alias}] {t.get('description','')}",
                    "parameters": t.get("input_schema", {"type":"object"})
                }
            })
        return wrapped
    except Exception as e:
        print(f"⚠️ No se pudieron cargar tools de {alias}: {e}")
        return []

def call_mcp(alias, tool_name, params):
    """Llama al /run del MCP correcto."""
    payload = {"tool_name": tool_name, "input": params}
    try:
        r = requests.post(f"{MCP_ENDPOINTS[alias]}/run", json=payload, timeout=20)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

def init_servers():
    """Inicializa cada MCP con /initialize."""
    for alias, base in MCP_ENDPOINTS.items():
        try:
            requests.post(f"{base}/initialize", timeout=5)
        except Exception as e:
            print(f"⚠️ No se pudo inicializar {alias}: {e}")

# ========== LOOP PRINCIPAL ==========
def main():
    print("🤖 Chatbot MCP (OpenAI + Local + Remoto)")
    print("Escribe 'salir' para terminar.\n")

    init_servers()

    # Combina todas las tools
    all_tools = []
    for alias, base in MCP_ENDPOINTS.items():
        all_tools.extend(fetch_tools(alias, base))
    if not all_tools:
        print("❌ No hay herramientas disponibles.")
        return

    history = [{
        "role": "system",
        "content": (
            "Eres un asistente conectado a dos servidores MCP:\n"
            "- 'local__' para gestión de tareas (crear, listar, completar, snooze).\n"
            "- 'remoto__' para finanzas (consultar saldo, registrar pagos).\n"
            "Si el usuario habla de tareas, usa el servidor local.\n"
            "Si habla de pagos o saldos, usa el servidor remoto.\n"
            "Responde siempre en español."
        )
    }]

    while True:
        user_input = input("👤 Tú: ").strip()
        if user_input.lower() in ("salir", "exit"):
            break

        history.append({"role": "user", "content": user_input})

        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=history,
                tools=all_tools,
                tool_choice="auto"
            )
            msg = resp.choices[0].message
            history.append(msg)

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    full_name = tc.function.name  # ej: local__get_pending_balance
                    args = json.loads(tc.function.arguments or "{}")

                    if "__" not in full_name:
                        print("⚠️ Tool inválida:", full_name)
                        continue
                    alias, bare = full_name.split("__", 1)

                    # Llamar al MCP correcto
                    mcp_resp = call_mcp(alias, bare, args)
                    if "output" in mcp_resp:
                        result = mcp_resp["output"]
                    else:
                        result = mcp_resp.get("error", {}).get("message", "Error desconocido")

                    print("🤖", result)
                    log_interaction(user_input, full_name, args, result)

                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": [
                            {
                                "type": "text",
                                "text": str(result)
                            }
                        ]
                    })
            else:
                print("🤖", msg.content)
                log_interaction(user_input, "LLM", {}, msg.content)

        except Exception as e:
            print("⚠️ Error:", e)

if __name__ == "__main__":
    main()
