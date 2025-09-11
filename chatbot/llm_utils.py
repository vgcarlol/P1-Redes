# llm_utils.py
import requests
import os
import re

OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "openai/gpt-3.5-turbo"

# Lista de herramientas declaradas (opcional para este modelo)
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_pending_balance",
            "description": "Obtiene el saldo pendiente de un usuario",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre del usuario a consultar"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "register_payment",
            "description": "Registra un pago al saldo del usuario",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre del usuario que realiza el pago"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Monto del pago a registrar"
                    }
                },
                "required": ["name", "amount"]
            }
        }
    }
]

def call_llm(user_input, tools=None, history=None):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = history[:] if history else []
    messages.append({"role": "user", "content": user_input})

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        result = response.json()
        _ = result["choices"][0]["message"]["content"]  # Para forzar error si no responde bien

        lowered = user_input.lower()

        # --- Detectar intención: obtener saldo ---
        if any(palabra in lowered for palabra in ["debe", "saldo", "cuánto"]):
            match = re.search(r"(?:de|debe|saldo de|cuánto debe a?|cuánto debe)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)", user_input, re.IGNORECASE)
            name = match.group(1) if match else "Usuario"
            return "get_pending_balance", {"name": name}

        # --- Detectar intención: registrar pago ---
        elif any(p in lowered for p in ["paga", "pagale", "págale", "dale", "pago", "registrar", "abonar"]):
            name_match = re.search(r"(?:a|para)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)", user_input)
            amount_match = re.search(r"\bQ?(\d+(?:\.\d+)?)\b", user_input)
            name = name_match.group(1) if name_match else "Usuario"
            amount = float(amount_match.group(1)) if amount_match else 0
            return "register_payment", {"name": name, "amount": amount}

        else:
            return None, {}

    except Exception as e:
        print("\u26a0\ufe0f Error al interpretar respuesta del LLM:", e)
        print("Respuesta cruda:", response.text)
        return None, {}
