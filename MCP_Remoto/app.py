# app.py
from flask import Flask, request, jsonify
from models import Session, Usuario
import json

app = Flask(__name__)

# Cargar spec.json
with open("spec.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

@app.route("/initialize", methods=["POST"])
def initialize():
    return jsonify({ "status": "ready" })

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
    session = Session()
    usuario = session.query(Usuario).filter_by(nombre=name).first()
    session.close()
    if not usuario:
        return error_response(f"Usuario '{name}' no encontrado.", code=404)
    return jsonify({ "output": usuario.saldo_pendiente })

def register_payment(params):
    name = params.get("name")
    amount = params.get("amount")
    if not name or amount is None:
        return error_response("Missing 'name' or 'amount' parameter", code=400)
    session = Session()
    usuario = session.query(Usuario).filter_by(nombre=name).first()
    if not usuario:
        session.close()
        return error_response(f"Usuario '{name}' no encontrado.", code=404)
    usuario.saldo_pendiente = max(usuario.saldo_pendiente - float(amount), 0)
    session.commit()
    new_balance = usuario.saldo_pendiente
    session.close()
    return jsonify({
        "output": f"Pago de Q{amount} registrado exitosamente. Nuevo saldo: Q{new_balance}"
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
    app.run(host="0.0.0.0", port=5000)
