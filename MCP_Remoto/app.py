# app.py
from flask import Flask, request, jsonify
import json
import pandas as pd

app = Flask(__name__)

# Cargar spec.json
with open("spec.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

CSV_FILE = "usuarios.csv"

@app.route("/initialize", methods=["POST"])
def initialize():
    return jsonify({"status": "ready"})

@app.route("/describe", methods=["POST"])
def describe():
    return jsonify(spec)

@app.route("/run", methods=["POST"])
def run():
    try:
        data = request.get_json()
        tool_name = data.get("tool_name")
        input_params = data.get("input", {})

        if tool_name == "get_pending_balance":
            return get_pending_balance(input_params)
        elif tool_name == "register_payment":
            return register_payment(input_params)
        else:
            return error_response("Tool not found", code=404)
    except Exception as e:
        return error_response(str(e), code=500)

def get_pending_balance(params):
    name = params.get("name")
    if not name:
        return error_response("Missing 'name' parameter", code=400)

    df = pd.read_csv(CSV_FILE)
    user_row = df[df['nombre'] == name]

    if user_row.empty:
        return error_response(f"Usuario '{name}' no encontrado.", code=404)

    saldo = float(user_row.iloc[0]['saldo_pendiente'])
    return jsonify({"output": f"Saldo pendiente de {name}: Q{saldo}"})

def register_payment(params):
    name = params.get("name")
    amount = params.get("amount")

    if not name or amount is None:
        return error_response("Missing 'name' or 'amount' parameter", code=400)

    df = pd.read_csv(CSV_FILE)
    idx = df.index[df['nombre'] == name]

    if idx.empty:
        return error_response(f"Usuario '{name}' no encontrado.", code=404)

    current_balance = float(df.loc[idx[0], 'saldo_pendiente'])
    new_balance = max(current_balance - float(amount), 0.0)

    df.loc[idx[0], 'saldo_pendiente'] = new_balance
    df.to_csv(CSV_FILE, index=False)

    return jsonify({
        "output": f"Pago de Q{amount} registrado para {name}. Nuevo saldo: Q{new_balance}"
    })

def error_response(message, code=500):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "type": "mcp_error"
        }
    }), code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
